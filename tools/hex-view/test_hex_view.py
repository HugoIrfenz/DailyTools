import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from hex_view import format_line, iter_chunks, non_negative_int, width_int


SCRIPT = Path(__file__).with_name("hex_view.py")


class HexViewTests(unittest.TestCase):
    def run_cli(self, *args: str, input_bytes: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_formats_hex_and_ascii(self) -> None:
        self.assertEqual(format_line(0, b"AB\x00\xff", 4), "00000000  41 42 00 ff  |AB..|")

    def test_partial_line_is_padded(self) -> None:
        self.assertEqual(format_line(16, b"A", 4), "00000010  41           |A|")

    def test_large_offset_expands_address(self) -> None:
        self.assertTrue(format_line(0x100000000, b"A", 1).startswith("100000000  41"))

    def test_iter_chunks_honors_offset_and_width(self) -> None:
        chunks = list(iter_chunks(io.BytesIO(b"0123456789"), offset=2, width=3))
        self.assertEqual(chunks, [(2, b"234"), (5, b"567"), (8, b"89")])

    def test_iter_chunks_honors_length(self) -> None:
        chunks = list(iter_chunks(io.BytesIO(b"abcdefgh"), length=5, width=4))
        self.assertEqual(chunks, [(0, b"abcd"), (4, b"e")])

    def test_zero_length_outputs_no_chunks(self) -> None:
        self.assertEqual(list(iter_chunks(io.BytesIO(b"abc"), length=0)), [])

    def test_offset_beyond_end_outputs_no_chunks(self) -> None:
        self.assertEqual(list(iter_chunks(io.BytesIO(b"abc"), offset=20)), [])

    def test_integer_parser_accepts_hex(self) -> None:
        self.assertEqual(non_negative_int("0x10"), 16)

    def test_width_parser_rejects_out_of_range(self) -> None:
        with self.assertRaises(Exception):
            width_int("65")

    def test_cli_reads_stdin(self) -> None:
        result = self.run_cli("--width", "4", input_bytes=b"AB\x00\xff")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"00000000  41 42 00 ff  |AB..|\n")

    def test_cli_reads_file_with_slice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.bin")
            path.write_bytes(bytes(range(16)))
            result = self.run_cli(str(path), "--offset", "0x4", "--length", "3")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"00000004  04 05 06", result.stdout)
        self.assertNotIn(b"07", result.stdout)

    def test_cli_empty_input_is_successful(self) -> None:
        result = self.run_cli(input_bytes=b"")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")

    def test_cli_reports_missing_file(self) -> None:
        result = self.run_cli("missing.bin")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"error:", result.stderr)

    def test_cli_rejects_negative_offset(self) -> None:
        result = self.run_cli("--offset", "-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"non-negative", result.stderr)

    def test_cli_rejects_zero_width(self) -> None:
        result = self.run_cli("--width", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"between 1 and 64", result.stderr)


if __name__ == "__main__":
    unittest.main()
