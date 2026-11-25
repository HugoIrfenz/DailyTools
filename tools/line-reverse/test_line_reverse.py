import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("line_reverse.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_blank_and_unterminated_lines(self):
        result = self.run_cli("-", payload=b"first\n\nlast")
        self.assertEqual((result.returncode, result.stdout), (0, b"last\n\nfirst\n"))

    def test_file_bom_unicode_separator(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes("﻿é\r\nx\u2028y".encode())
            result = self.run_cli(str(path))
        self.assertEqual((result.returncode, result.stdout), (0, "y\nx\né\n".encode()))

    def test_empty_and_invalid_input(self):
        self.assertEqual(self.run_cli("-", payload=b"").stdout, b"")
        result = self.run_cli("-", payload=b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

