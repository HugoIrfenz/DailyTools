import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("trailing_space_check.py")


class TrailingSpaceTests(unittest.TestCase):
    def run_cli(self, *paths, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *paths], input=payload,
                              capture_output=True)

    def test_stdin_mixed_newlines_and_unterminated_line(self):
        result = self.run_cli("-", payload=b"clean\r\n \t\rnext\t")
        self.assertEqual(result.returncode, 1)
        self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], [
            {"file": "-", "line": 2, "count": 2},
            {"file": "-", "line": 3, "count": 1},
        ])

    def test_bom_and_non_ascii_space(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.txt"
            path.write_bytes("﻿space \n".encode())
            result = self.run_cli(path)
        self.assertEqual((result.returncode, result.stdout), (0, b""))

    def test_file_error_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.txt"
            bad.write_bytes(b"\xff")
            result = self.run_cli(bad, "-", payload=b"trailing \n")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["count"], 1)
        self.assertIn(b"bad.txt", result.stderr)
