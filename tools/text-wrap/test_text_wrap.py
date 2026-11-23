import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("text_wrap.py")


class WrapTests(unittest.TestCase):
    def run_cli(self, payload, width="9", path="-"):
        return subprocess.run([sys.executable, SCRIPT, str(path), "--width", width],
                              input=payload, capture_output=True)

    def test_example_and_long_words(self):
        result = self.run_cli(b"one two three four\n")
        self.assertEqual((result.returncode, result.stdout), (0, b"one two\nthree\nfour\n"))
        self.assertEqual(self.run_cli(b"long-word-here", "4").stdout, b"long-word-here\n")

    def test_file_bom_crlf_and_paragraphs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes("﻿é   abc\r\ndef\r\n \t\r\nnext".encode())
            result = self.run_cli(b"", "7", path)
        self.assertEqual((result.returncode, result.stdout), (0, "é abc\ndef\n\nnext\n".encode()))

    def test_empty_invalid_utf8_and_width(self):
        self.assertEqual(self.run_cli(b" \n\n").stdout, b"")
        result = self.run_cli(b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        result = self.run_cli(b"text", "0")
        self.assertEqual((result.returncode, result.stdout), (2, b""))
