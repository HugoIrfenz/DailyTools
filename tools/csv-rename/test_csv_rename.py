import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("csv_rename.py")


class RenameTests(unittest.TestCase):
    def run_cli(self, data, *args, path="-"):
        return subprocess.run([sys.executable, SCRIPT, str(path), *args],
                              input=data, capture_output=True)

    def test_rename_and_multiline_value(self):
        result = self.run_cli(b'id,name\n1,"Ana\nBudi"\n', "--rename", "name", "full_name")
        self.assertEqual((result.returncode, result.stdout),
                         (0, b'id,full_name\r\n1,"Ana\nBudi"\r\n'))

    def test_simultaneous_swap_file_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_bytes(b"\xef\xbb\xbfa,b\r\n1,2\r\n")
            result = self.run_cli(b"", "--rename", "a", "b", "--rename", "b", "a", path=path)
        self.assertEqual((result.returncode, result.stdout), (0, b"b,a\r\n1,2\r\n"))

    def test_invalid_headers_and_mappings(self):
        for data, args in ((b"a,b\n", ("--rename", "a", "b")),
                           (b"a,a\n", ("--rename", "a", "x")),
                           (b"a,b\n", ("--rename", "c", "x")),
                           (b"a,b\n", ("--rename", "a", ""))):
            with self.subTest(data=data, args=args):
                result = self.run_cli(data, *args)
                self.assertEqual((result.returncode, result.stdout), (1, b""))

    def test_ragged_rows_and_repeated_source(self):
        result = self.run_cli(b"a,b\n1\n", "--rename", "a", "x")
        self.assertEqual((result.returncode, result.stdout), (1, b"x,b\r\n"))
        result = self.run_cli(b"a\n", "--rename", "a", "x", "--rename", "a", "y")
        self.assertEqual((result.returncode, result.stdout), (2, b""))
