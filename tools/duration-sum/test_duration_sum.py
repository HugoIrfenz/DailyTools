import json
from pathlib import Path
import subprocess
import sys
import unittest

from duration_sum import normalize, parse_duration

SCRIPT = Path(__file__).with_name("duration_sum.py")


class DurationTests(unittest.TestCase):
    def test_compound(self):
        self.assertEqual(parse_duration("1h30m 5s"), 5405000000)

    def test_each_unit(self):
        for text, expected in [("1d", 86400000000), ("1h", 3600000000),
                               ("1m", 60000000), ("1s", 1000000),
                               ("1ms", 1000), ("1us", 1)]:
            self.assertEqual(parse_duration(text), expected)

    def test_exact_fractions(self):
        self.assertEqual(parse_duration("0.1s 0.2s"), 300000)
        self.assertEqual(parse_duration("0.0000001m"), 6)
        self.assertEqual(parse_duration("1.0000000us"), 1)

    def test_sign_whole_expression(self):
        self.assertEqual(parse_duration(" - 1h 30m "), -5400000000)
        self.assertEqual(parse_duration("+2s"), 2000000)

    def test_repeated_units(self):
        self.assertEqual(parse_duration("30m30m"), 3600000000)

    def test_invalid_grammar(self):
        for text in ["", "+", "1", "1w", "1S", "1e3s", "1 s", ".5s", "1.s",
                     "1s garbage", "1h-2m", "1h+2m", "NaNs", "１２s"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_duration(text)

    def test_reject_fractional_microseconds(self):
        for text in ["0.1us", "0.0001ms", "0.0000001s"]:
            with self.assertRaises(ValueError):
                parse_duration(text)

    def test_length_limit(self):
        with self.assertRaises(ValueError):
            parse_duration("1" * 4096 + "s")

    def test_normalize_and_roundtrip(self):
        self.assertEqual(normalize(0), "0s")
        self.assertEqual(normalize(90061001002), "1d 1h 1m 1s 1ms 2us")
        for value in [-90061001002, -1, 0, 1, 999999, 3600000000]:
            self.assertEqual(parse_duration(normalize(value)), value)

    def test_large_integer(self):
        self.assertEqual(parse_duration("10000000000000000000us"), 10**19)

    def test_cli_text_and_json(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "1h30m", "45m"],
                             capture_output=True, text=True)
        self.assertEqual((run.returncode, run.stdout), (0, "2h 15m\n"))
        run = subprocess.run([sys.executable, str(SCRIPT), "--json", "--", "1h", "-90m"],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(json.loads(run.stdout),
                         {"microseconds": -1800000000, "normalized": "-30m"})

    def test_cli_invalid_no_stdout(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "1fortnight"],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, "")
        self.assertTrue(run.stderr)


if __name__ == "__main__":
    unittest.main()
