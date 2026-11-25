import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("decimal_round.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_rounding_ties(self):
        result = self.run_cli("2.345", "2.355", "--places", "2")
        self.assertEqual((result.returncode, result.stdout), (0, b"2.34\n2.36\n"))
        result = self.run_cli("--mode", "half-up", "--places", "2", "--", "-2.345")
        self.assertEqual((result.returncode, result.stdout), (0, b"-2.35\n"))

    def test_exponent_and_zero_places(self):
        result = self.run_cli("1e3", "2.5", "--places", "0")
        self.assertEqual((result.returncode, result.stdout), (0, b"1000\n2\n"))

    def test_invalid_value_has_no_partial_output(self):
        for raw in ("NaN", "Infinity", "bad", "1e1001"):
            result = self.run_cli("1", raw)
            self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertEqual(self.run_cli("1", "--places", "-1").returncode, 2)

