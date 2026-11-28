import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("csv_head.py")
class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)

    def test_multiline_and_limit(self):
        result = self.run_cli("-", "--rows", "1", payload=b'id,name\n1,"Ana\nBudi"\n2,X\n')
        self.assertEqual((result.returncode, result.stdout), (0, b'id,name\r\n1,"Ana\nBudi"\r\n'))
    def test_file_bom_header_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_bytes(b"\xef\xbb\xbfa,b\n1,2\n")
            result = self.run_cli(str(path), "--rows", "0")
        self.assertEqual((result.returncode, result.stdout), (0, b"a,b\r\n"))
    def test_invalid_count_and_record(self):
        self.assertEqual(self.run_cli("-", "--rows", "-1").returncode, 2)
        result = self.run_cli("-", payload=b'a\n"unfinished')
        self.assertEqual((result.returncode, result.stdout), (1, b"a\r\n"))

