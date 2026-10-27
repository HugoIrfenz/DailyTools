import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from unicode_normalize import decode_utf8, normalize_text, read_input


SCRIPT = Path(__file__).with_name("unicode_normalize.py")


class UnicodeNormalizeTests(unittest.TestCase):
    def run_cli(self, *args: str, input_bytes: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_nfc_composes_decomposed_character(self) -> None:
        self.assertEqual(normalize_text("Cafe\u0301", "NFC"), "Caf\u00e9")

    def test_nfd_decomposes_composed_character(self) -> None:
        self.assertEqual(normalize_text("\u00e9", "NFD"), "e\u0301")

    def test_nfkc_applies_compatibility_mapping(self) -> None:
        self.assertEqual(normalize_text("\ufb03", "NFKC"), "ffi")

    def test_nfkd_decomposes_fullwidth_text(self) -> None:
        self.assertEqual(normalize_text("\uff21\uff22", "NFKD"), "AB")

    def test_empty_text_is_unchanged(self) -> None:
        self.assertEqual(normalize_text("", "NFC"), "")

    def test_newline_bytes_are_preserved(self) -> None:
        value = "a\r\nCafe\u0301\rnext\n"
        self.assertEqual(normalize_text(value, "NFC"), "a\r\nCaf\u00e9\rnext\n")

    def test_invalid_form_in_function_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_text("text", "BAD")

    def test_decode_utf8_rejects_invalid_bytes(self) -> None:
        with self.assertRaises(UnicodeDecodeError):
            decode_utf8(b"\xff")

    def test_read_input_reads_path_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.txt")
            path.write_bytes("Caf\u00e9".encode())
            self.assertEqual(read_input(str(path)), "Caf\u00e9".encode())

    def test_cli_normalizes_stdin_as_utf8(self) -> None:
        result = self.run_cli("--form", "NFC", input_bytes="Cafe\u0301\n".encode())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "Caf\u00e9\n".encode())
        self.assertEqual(result.stderr, b"")

    def test_cli_normalizes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.txt")
            path.write_bytes("\ufb03".encode())
            result = self.run_cli(str(path), "--form", "NFKC")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"ffi")

    def test_check_passes_for_normalized_input(self) -> None:
        result = self.run_cli("--check", input_bytes="Caf\u00e9".encode())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"normalized (NFC)", result.stderr)

    def test_check_fails_when_change_is_required(self) -> None:
        result = self.run_cli("--check", input_bytes="Cafe\u0301".encode())
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"normalization required (NFC)", result.stderr)

    def test_cli_rejects_invalid_utf8_without_traceback(self) -> None:
        result = self.run_cli(input_bytes=b"valid\xffinvalid")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"error:", result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_cli_reports_missing_file(self) -> None:
        result = self.run_cli("does-not-exist.txt")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"error:", result.stderr)

    def test_cli_rejects_unknown_form(self) -> None:
        result = self.run_cli("--form", "BAD", input_bytes=b"text")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
