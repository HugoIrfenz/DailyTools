import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("text_indent.py")
class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)

    def test_prefix_and_skip_blank(self):
        result = self.run_cli("-", "--prefix", "> ", "--skip-blank", payload=b"a\n  \nb")
        self.assertEqual((result.returncode, result.stdout), (0, b"> a\n  \n> b\n"))
    def test_file_unicode_bom_and_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes("﻿é\r\nx".encode())
            result = self.run_cli(str(path))
        self.assertEqual((result.returncode, result.stdout), (0, "    é\n    x\n".encode()))
    def test_invalid_prefix_and_encoding(self):
        self.assertEqual(self.run_cli("-", "--prefix", "x\n").returncode, 2)
        result = self.run_cli("-", payload=b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

