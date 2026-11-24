import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("tab_expand.py")


class TabTests(unittest.TestCase):
    def run_cli(self, data, path="-", size="4"):
        return subprocess.run([sys.executable, SCRIPT, str(path), "--size", size],
                              input=data, capture_output=True)

    def test_column_stops_and_crlf(self):
        result = self.run_cli(b"a\tb\r\n\tend\rx\ty")
        self.assertEqual((result.returncode, result.stdout),
                         (0, b"a   b\r\n    end\rx   y"))

    def test_file_bom_unicode_and_no_added_newline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes("﻿é\tx".encode())
            result = self.run_cli(b"", path)
        self.assertEqual((result.returncode, result.stdout), (0, "é   x".encode()))

    def test_invalid_size_and_encoding(self):
        for size in ("0", "257"):
            result = self.run_cli(b"text", size=size)
            self.assertEqual((result.returncode, result.stdout), (2, b""))
        result = self.run_cli(b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
