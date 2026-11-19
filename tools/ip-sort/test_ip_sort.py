import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("ip_sort.py")


class CLITests(unittest.TestCase):
    def run_cli(self, payload, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_numeric_order_and_equivalent_ipv6(self):
        result = self.run_cli(b"10.0.0.10\n0:0:0:0:0:0:0:1\n10.0.0.2\n::1\n", "-")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"10.0.0.2\n10.0.0.10\n::1\n")

    def test_invalid_input_produces_no_partial_output(self):
        for address in (b"bad", b"fe80::1%eth0", b"10.0.0.0/24"):
            with self.subTest(address=address):
                result = self.run_cli(b"127.0.0.1\n" + address, "-")
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(b"line 2", result.stderr)

    def test_file_bom_and_blanks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes(b"\xef\xbb\xbf  ::1  \n\n")
            result = self.run_cli(b"", str(path))
        self.assertEqual((result.returncode, result.stdout), (0, b"::1\n"))

