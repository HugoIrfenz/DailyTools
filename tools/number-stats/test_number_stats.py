import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("number_stats.py")


class StatsTests(unittest.TestCase):
    def run_cli(self, data, path="-"):
        return subprocess.run([sys.executable, SCRIPT, str(path)], input=data, capture_output=True)

    def test_exact_decimal_sum(self):
        result = self.run_cli(b"0.1\n0.2\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout),
                         {"count": 2, "min": "0.1", "max": "0.2", "sum": "0.3", "mean": "0.15"})

    def test_file_bom_negatives_and_exponents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes(b"\xef\xbb\xbf-1e2\n\n50\n")
            result = self.run_cli(b"", path)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["mean"], "-25")

    def test_invalid_nonfinite_empty_and_exponent_bounds(self):
        for data in (b"", b"oops", b"NaN", b"Infinity", b"1e10001"):
            with self.subTest(data=data):
                result = self.run_cli(data)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
