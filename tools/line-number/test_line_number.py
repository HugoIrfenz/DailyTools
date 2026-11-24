import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("line_number.py")


class NumberTests(unittest.TestCase):
    def run_cli(self, data, path="-", start="1"):
        return subprocess.run([sys.executable, SCRIPT, str(path), "--start", start],
                              input=data, capture_output=True)

    def test_start_blank_and_unterminated_lines(self):
        result = self.run_cli(b"alpha\n\nbeta", start="10")
        self.assertEqual((result.returncode, result.stdout),
                         (0, b"10\talpha\n11\t\n12\tbeta\n"))

    def test_file_bom_crlf_unicode_separator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes("﻿é\r\nx\u2028y".encode())
            result = self.run_cli(b"", path)
        self.assertEqual((result.returncode, result.stdout), (0, "1\té\n2\tx\n3\ty\n".encode()))

    def test_empty_and_invalid_utf8(self):
        self.assertEqual(self.run_cli(b"").stdout, b"")
        result = self.run_cli(b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
