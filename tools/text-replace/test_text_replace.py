import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("text_replace.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_literal_nonoverlap_and_count(self):
        result = self.run_cli("aa", "b", "-", payload=b"aaa")
        self.assertEqual((result.returncode, result.stdout), (0, b"ba"))
        self.assertEqual(self.run_cli(".", "x", "-", "--count", "1", payload=b"a.b.c").stdout, b"axb.c")
        self.assertEqual(self.run_cli("a", "b", "-", "--count", "0", payload=b"a").stdout, b"a")

    def test_file_unicode_bom_crlf(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes("﻿é\r\né".encode())
            result = self.run_cli("é", "x", str(path))
        self.assertEqual((result.returncode, result.stdout), (0, b"x\r\nx"))

    def test_invalid_options_and_utf8(self):
        self.assertEqual(self.run_cli("", "x", "-").returncode, 2)
        self.assertEqual(self.run_cli("x", "y", "-", "--count", "-1").returncode, 2)
        result = self.run_cli("x", "y", "-", payload=b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

