import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import eol_inspect as tool

SCRIPT = Path(__file__).with_name("eol_inspect.py")


class EolInspectTests(unittest.TestCase):
    def cli(self, *args, raw=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              input=raw, capture_output=True)

    def test_empty(self):
        report = tool.inspect([])
        self.assertEqual(report["logical_lines"], 0)
        self.assertFalse(report["ends_with_newline"])

    def test_lf_crlf_cr_separately(self):
        for raw, key in ((b'a\nb\n', "lf"), (b'a\r\nb\r\n', "crlf"), (b'a\rb\r', "cr")):
            with self.subTest(key=key):
                report = tool.inspect([raw])
                self.assertEqual(report[key], 2)
                self.assertEqual(report["logical_lines"], 2)
                self.assertFalse(report["mixed"])

    def test_mixed_and_missing_final_newline(self):
        report = tool.inspect([b'a\nb\r\nc\rd'])
        self.assertTrue(report["mixed"])
        self.assertEqual(report["logical_lines"], 4)
        self.assertFalse(report["ends_with_newline"])

    def test_crlf_split_across_chunks(self):
        self.assertEqual(tool.inspect([b'a\r', b'', b'\nb\r', b'\n']),
                         tool.inspect([b'a\r\nb\r\n']))

    def test_repeated_cr_and_final_cr(self):
        report = tool.inspect([b'\r', b'\r', b'\n', b'\r'])
        self.assertEqual(report["cr"], 2)
        self.assertEqual(report["crlf"], 1)
        self.assertEqual(report["logical_lines"], 3)

    def test_binary_bytes_need_no_utf8(self):
        report = tool.inspect([b'\xff\x00\n'])
        self.assertEqual(report["bytes"], 3)
        self.assertEqual(report["lf"], 1)

    def test_text_without_newline_and_blank_lines(self):
        self.assertEqual(tool.inspect([b'abc'])["logical_lines"], 1)
        self.assertEqual(tool.inspect([b'\n\n'])["logical_lines"], 2)

    def test_all_chunk_boundaries_match(self):
        raw = b'\r\n\xff\rX\n\r\r\nend'
        expected = tool.inspect([raw])
        for width in range(1, len(raw)+1):
            self.assertEqual(tool.inspect(raw[i:i+width] for i in range(0, len(raw), width)),
                             expected)

    def test_cli_json_and_check(self):
        result = self.cli("-", "--json", "--check", raw=b'a\r\n')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["crlf"], 1)
        self.assertEqual(self.cli("-", "--check", raw=b'a').returncode, 1)
        self.assertEqual(self.cli("-", "--check", raw=b'\r\n\n').returncode, 1)
        self.assertEqual(self.cli("-", "--check", raw=b'').returncode, 0)

    def test_cli_file_unchanged_and_read_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "file.bin"
            path.write_bytes(b'a\n')
            result = self.cli(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn(b'LF: 1', result.stdout)
            self.assertEqual(path.read_bytes(), b'a\n')
            missing = self.cli(Path(folder) / "missing")
            self.assertEqual(missing.returncode, 2)
            self.assertEqual(missing.stdout, b'')


if __name__ == "__main__":
    unittest.main()
