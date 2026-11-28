import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("line_filter.py")
class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)

    def test_unicode_casefold_and_invert(self):
        result = self.run_cli("STRASSE", "-", "--ignore-case", payload="Straße\nother".encode())
        self.assertEqual((result.returncode, result.stdout), (0, "Straße\n".encode()))
        self.assertEqual(self.run_cli("x", "-", "--invert", payload=b"x\ny").stdout, b"y\n")
    def test_file_bom_and_empty_pattern(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes(b"\xef\xbb\xbfa\r\n\r\nb")
            result = self.run_cli("", str(path))
        self.assertEqual((result.returncode, result.stdout), (0, b"a\n\nb\n"))
    def test_invalid_utf8(self):
        result = self.run_cli("x", "-", payload=b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

