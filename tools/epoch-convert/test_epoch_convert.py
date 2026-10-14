from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import unittest
import epoch_convert as tool

SCRIPT = Path(__file__).with_name("epoch_convert.py")


class EpochConvertTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_zero_and_positive_fraction(self):
        self.assertEqual(tool.report(tool.parse_epoch("0"))["seconds"], "0")
        result = tool.report(tool.parse_epoch("1.234567"))
        self.assertEqual(result["milliseconds"], "1234.567")
        self.assertEqual(result["utc"], "1970-01-01T00:00:01.234567+00:00")

    def test_negative_microsecond(self):
        result = tool.report(tool.parse_epoch("-0.000001"))
        self.assertEqual(result["utc"], "1969-12-31T23:59:59.999999+00:00")
        self.assertEqual(result["seconds"], "-0.000001")
        self.assertEqual(result["milliseconds"], "-0.001")

    def test_millisecond_input_matches_second_input(self):
        self.assertEqual(tool.parse_epoch("1234.567", "milliseconds"),
                         tool.parse_epoch("1.234567"))

    def test_offset_and_leap_date(self):
        result = tool.report(tool.parse_iso("2000-02-29T07:00:00+07:00"))
        self.assertEqual(result["utc"], "2000-02-29T00:00:00.000000+00:00")
        self.assertEqual(result["seconds"], "951782400")

    def test_pre_epoch_offset(self):
        self.assertEqual(tool.report(tool.parse_iso("1970-01-01T01:00:00+02:00"))["seconds"],
                         "-3600")

    def test_datetime_boundaries_roundtrip(self):
        for value in (datetime(1, 1, 1, tzinfo=timezone.utc),
                      datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)):
            self.assertEqual(tool.parse_epoch(tool.report(value)["seconds"]), value)

    def test_decimal_roundtrip_no_float(self):
        for raw in ("0.000001", "1700000000.123456", "-1234567.987654", "001.500000"):
            value = tool.parse_epoch(raw)
            self.assertEqual(tool.parse_epoch(tool.report(value)["seconds"]), value)

    def test_invalid_numbers_and_excess_precision(self):
        for raw, unit in (("NaN", "seconds"), ("1e3", "seconds"), ("1.", "seconds"),
                          ("0.0000001", "seconds"), ("1.0001", "milliseconds"),
                          ("999999999999999999999", "seconds")):
            with self.subTest(raw=raw), self.assertRaises((ValueError, OverflowError)):
                tool.parse_epoch(raw, unit)

    def test_naive_invalid_and_overprecise_iso(self):
        for raw in ("1970-01-01T00:00:00", "2026-02-29T00:00:00Z",
                    "1970-01-01T00:00:00.1234567Z", "1970-01-01", "bad"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                tool.parse_iso(raw)

    def test_cli_json_and_text(self):
        result = self.cli("from-epoch", "1700000000123", "--unit", "milliseconds", "--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["seconds"], "1700000000.123")
        result = self.cli("to-epoch", "1970-01-01T07:00:00+07:00")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Seconds: 0", result.stdout)

    def test_cli_invalid_exit_two(self):
        for args in (("from-epoch", "nan"), ("to-epoch", "1970-01-01"),
                     ("from-epoch", "0", "--unit", "minutes")):
            result = self.cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
