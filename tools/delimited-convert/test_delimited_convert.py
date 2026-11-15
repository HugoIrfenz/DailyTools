import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("delimited_convert.py")


class DelimitedConvertTests(unittest.TestCase):
    def run_cli(self, payload, source="-", from_format="semicolon", to_format="comma"):
        return subprocess.run(
            [sys.executable, SCRIPT, source, "--from", from_format, "--to", to_format],
            input=payload, capture_output=True,
        )

    def test_quotes_multiline_and_new_delimiter(self):
        result = self.run_cli(b'a;b\r\n"a;1";"x,y\r\nz""q"\r\n')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'a,b\r\na;1,"x,y\r\nz""q"\r\n')

    def test_bom_and_ragged_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.tsv"
            path.write_bytes(b'\xef\xbb\xbfa\tb\n1\n')
            result = self.run_cli(b"", path, "tab", "pipe")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'a|b\r\n1\r\n')

    def test_unterminated_quote(self):
        result = self.run_cli(b'a;b\n"unfinished')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b'a,b\r\n')
        self.assertIn(b"delimited-convert:", result.stderr)
