import argparse
from datetime import date
import subprocess
import sys
from pathlib import Path
import unittest

from date_range import dates, parse_date


class RangeTests(unittest.TestCase):
    def test_includes_leap_day_and_endpoints(self):
        self.assertEqual(list(dates(date(2024, 2, 28), date(2024, 3, 1))),
                         ["2024-02-28", "2024-02-29", "2024-03-01"])

    def test_weekdays_and_maximum_date(self):
        self.assertEqual(list(dates(date(2026, 11, 13), date(2026, 11, 16), True)),
                         ["2026-11-13", "2026-11-16"])
        self.assertEqual(list(dates(date.max, date.max)), ["9999-12-31"])

    def test_invalid_date_and_reverse_range(self):
        for raw in ("20240101", "2026-02-29"):
            with self.subTest(raw=raw), self.assertRaises(argparse.ArgumentTypeError):
                parse_date(raw)
        script = Path(__file__).with_name("date_range.py")
        result = subprocess.run([sys.executable, script, "2026-11-16", "2026-11-15"],
                                capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
