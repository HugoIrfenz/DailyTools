import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("integer_base.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_signed_zero_and_mixed_case(self):
        for value, source, target, expected in (("Ff", 16, 2, b"11111111\n"),
                ("-255", 10, 16, b"-ff\n"), ("-0", 10, 36, b"0\n"),
                ("z", 36, 10, b"35\n")):
            with self.subTest(value=value):
                result = self.run_cli("--from", str(source), "--to", str(target), "--", value)
                self.assertEqual((result.returncode, result.stdout), (0, expected))

    def test_invalid_digits_and_prefixes(self):
        for value in ("0xff", "1_0", " 10", "2", ""):
            with self.subTest(value=value):
                result = self.run_cli(value, "--from", "2", "--to", "10")
                self.assertEqual((result.returncode, result.stdout), (1, b""))

