import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("text_dedent.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_common_indent_and_mixed_whitespace(self):
        result = self.run_cli("-", payload=b"    a\n      b\n")
        self.assertEqual((result.returncode, result.stdout), (0, b"a\n  b\n"))
        self.assertEqual(self.run_cli("-", payload=b"\ta\n    b").stdout, b"\ta\n    b")

    def test_file_bom_and_crlf(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes("﻿  é\r\n  x".encode())
            result = self.run_cli(str(path))
        self.assertEqual((result.returncode, result.stdout), (0, "é\nx".encode()))

    def test_invalid_utf8(self):
        result = self.run_cli("-", payload=b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

