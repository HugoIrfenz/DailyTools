from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import unittest
from zoneinfo import ZoneInfo

import cron_next as tool


SCRIPT = Path(__file__).with_name("cron_next.py")
UTC = ZoneInfo("UTC")


class CronNextTests(unittest.TestCase):
    def next(self, expression, after, count=1, zone=UTC, years=5):
        schedule = tool.CronSchedule.parse(expression)
        return schedule.next_occurrences(after, zone, count, years)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_lists_ranges_steps_and_names(self):
        schedule = tool.CronSchedule.parse("0,30 9-17/2 1,15 JAN-MAR MON-FRI")
        self.assertEqual(schedule.minute.values, {0, 30})
        self.assertEqual(schedule.hour.values, {9, 11, 13, 15, 17})
        self.assertEqual(schedule.month.values, {1, 2, 3})
        self.assertEqual(schedule.weekday.values, {1, 2, 3, 4, 5})

    def test_invalid_expressions(self):
        invalid = [
            "* * * *", "60 * * * *", "* 5-2 * * *", "*/0 * * * *",
            "5/2 * * * *", "*, * * * *", "* * * FOO *", "* * * * 8",
            "* * * * MON--FRI", "* * * * */x",
        ]
        for expression in invalid:
            with self.subTest(expression=expression):
                with self.assertRaises(tool.CronError):
                    tool.CronSchedule.parse(expression)

    def test_weekday_schedule_and_strictly_after(self):
        after = datetime.fromisoformat("2026-10-09T16:50:00+07:00")
        zone = ZoneInfo("Asia/Jakarta")
        found = self.next("*/15 9-17 * * MON-FRI", after, 3, zone)
        self.assertEqual([x.isoformat(timespec="minutes") for x in found], [
            "2026-10-09T17:00+07:00",
            "2026-10-09T17:15+07:00",
            "2026-10-09T17:30+07:00",
        ])
        exact = datetime.fromisoformat("2026-10-09T17:00:00+07:00")
        self.assertEqual(self.next("0 17 * * *", exact, zone=zone)[0].day, 10)

    def test_day_of_month_and_weekday_use_or_when_both_restricted(self):
        after = datetime(2026, 5, 1, tzinfo=UTC)
        found = self.next("0 0 15 * MON", after, 3)
        self.assertEqual([(x.month, x.day) for x in found], [(5, 4), (5, 11), (5, 15)])

    def test_unrestricted_day_field_does_not_force_or_match(self):
        after = datetime(2026, 5, 1, tzinfo=UTC)
        mondays = self.next("0 0 * * MON", after, 2)
        fifteenths = self.next("0 0 15 * *", after, 2)
        self.assertEqual([x.day for x in mondays], [4, 11])
        self.assertEqual([(x.month, x.day) for x in fifteenths], [(5, 15), (6, 15)])

    def test_leap_day_and_month_name(self):
        after = datetime(2027, 1, 1, tzinfo=UTC)
        found = self.next("0 12 29 FEB *", after)
        self.assertEqual(found[0].isoformat(timespec="minutes"), "2028-02-29T12:00+00:00")

    def test_sunday_zero_seven_and_name_are_equivalent(self):
        schedules = [tool.CronSchedule.parse(f"0 0 * * {value}")
                     for value in ("0", "7", "SUN")]
        self.assertTrue(all(s.weekday.values == {0} for s in schedules))

    def test_timezone_conversion(self):
        start = datetime.fromisoformat("2026-10-09T16:59:30+07:00")
        found = self.next("0 17 * * *", start, zone=ZoneInfo("Asia/Jakarta"))
        self.assertEqual(found[0].utcoffset().total_seconds(), 7 * 3600)
        self.assertEqual(found[0].hour, 17)

    def test_dst_gap_is_skipped(self):
        zone = ZoneInfo("America/New_York")
        start = datetime.fromisoformat("2026-03-07T03:00:00-05:00")
        found = self.next("30 2 * * *", start, zone=zone)
        self.assertEqual(found[0].isoformat(timespec="minutes"), "2026-03-09T02:30-04:00")

    def test_dst_fold_returns_both_real_instants(self):
        zone = ZoneInfo("America/New_York")
        start = datetime.fromisoformat("2026-11-01T00:00:00-04:00")
        found = self.next("30 1 * * *", start, 2, zone)
        self.assertEqual([x.isoformat(timespec="minutes") for x in found], [
            "2026-11-01T01:30-04:00", "2026-11-01T01:30-05:00"])

    def test_impossible_schedule_respects_horizon(self):
        start = datetime(2026, 1, 1, tzinfo=UTC)
        self.assertEqual(self.next("0 0 30 FEB *", start, years=1), [])

    def test_cli_text_and_json_examples(self):
        args = ("*/15 9-17 * * MON-FRI", "--from", "2026-10-09T16:50:00",
                "--timezone", "Asia/Jakarta", "--count", "3")
        text = self.cli(*args)
        self.assertEqual(text.returncode, 0)
        self.assertIn("2026-10-09T17:30+07:00", text.stdout)
        structured = self.cli(*args, "--json")
        self.assertEqual(structured.returncode, 0)
        self.assertEqual(len(json.loads(structured.stdout)["occurrences"]), 3)

    def test_cli_validation_and_no_match_exit_codes(self):
        self.assertEqual(self.cli("bad").returncode, 2)
        self.assertEqual(self.cli("* * * * *", "--timezone", "Mars/Olympus").returncode, 2)
        self.assertEqual(self.cli("* * * * *", "--count", "0").returncode, 2)
        result = self.cli("0 0 30 FEB *", "--from", "2026-01-01",
                          "--max-years", "1", "--json")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
