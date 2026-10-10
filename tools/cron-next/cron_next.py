#!/usr/bin/env python3
"""Validate a five-field cron expression and print its next occurrences."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


MONTHS = {name: number for number, name in enumerate(
    ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
     "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}
WEEKDAYS = {name: number for number, name in enumerate(
    ("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"))}


class CronError(ValueError):
    pass


@dataclass(frozen=True)
class Field:
    values: frozenset
    restricted: bool


def parse_atom(text, minimum, maximum, names, label):
    upper = text.upper()
    if upper in names:
        return names[upper]
    try:
        value = int(text)
    except ValueError as exc:
        raise CronError(f"{label}: invalid value {text!r}") from exc
    if not minimum <= value <= maximum:
        raise CronError(f"{label}: {value} is outside {minimum}-{maximum}")
    return value


def parse_field(text, minimum, maximum, label, names=None, sunday=False):
    names = names or {}
    if not text or any(not part for part in text.split(",")):
        raise CronError(f"{label}: empty list item")
    values = set()
    for part in text.split(","):
        if part.count("/") > 1:
            raise CronError(f"{label}: malformed step {part!r}")
        base, slash, step_text = part.partition("/")
        if slash:
            try:
                step = int(step_text)
            except ValueError as exc:
                raise CronError(f"{label}: step must be an integer") from exc
            if step <= 0:
                raise CronError(f"{label}: step must be greater than zero")
        else:
            step = 1
        if base == "*":
            start, end = minimum, maximum
        elif "-" in base:
            if base.count("-") != 1:
                raise CronError(f"{label}: malformed range {base!r}")
            first, last = base.split("-")
            start = parse_atom(first, minimum, maximum, names, label)
            end = parse_atom(last, minimum, maximum, names, label)
            if start > end:
                raise CronError(f"{label}: descending ranges are not supported")
        else:
            if slash:
                raise CronError(f"{label}: a step requires '*' or a range")
            start = end = parse_atom(base, minimum, maximum, names, label)
        values.update(range(start, end + 1, step))
    if sunday:
        values = {0 if value == 7 else value for value in values}
        domain = set(range(7))
    else:
        domain = set(range(minimum, maximum + 1))
    return Field(frozenset(values), values != domain)


@dataclass(frozen=True)
class CronSchedule:
    expression: str
    minute: Field
    hour: Field
    day: Field
    month: Field
    weekday: Field

    @classmethod
    def parse(cls, expression):
        parts = expression.split()
        if len(parts) != 5:
            raise CronError("expected five fields: minute hour day-of-month month day-of-week")
        minute, hour, day, month, weekday = parts
        return cls(
            expression,
            parse_field(minute, 0, 59, "minute"),
            parse_field(hour, 0, 23, "hour"),
            parse_field(day, 1, 31, "day-of-month"),
            parse_field(month, 1, 12, "month", MONTHS),
            parse_field(weekday, 0, 7, "day-of-week", WEEKDAYS, sunday=True),
        )

    def matches(self, local):
        if (local.minute not in self.minute.values or
                local.hour not in self.hour.values or
                local.month not in self.month.values):
            return False
        day_match = local.day in self.day.values
        cron_weekday = (local.weekday() + 1) % 7
        weekday_match = cron_weekday in self.weekday.values
        if not self.day.restricted and not self.weekday.restricted:
            return True
        if not self.day.restricted:
            return weekday_match
        if not self.weekday.restricted:
            return day_match
        return day_match or weekday_match

    def next_occurrences(self, after, zone, count=5, max_years=5):
        current = after.astimezone(timezone.utc).replace(second=0, microsecond=0)
        current += timedelta(minutes=1)
        deadline = current + timedelta(days=366 * max_years)
        found = []
        while current <= deadline and len(found) < count:
            local = current.astimezone(zone)
            if self.matches(local):
                found.append(local)
            current += timedelta(minutes=1)
        return found


def bounded_integer(minimum, maximum):
    def parse(value):
        try:
            number = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"must be between {minimum} and {maximum}")
        return number
    return parse


def parse_time(value, zone):
    if value is None:
        return datetime.now(zone)
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CronError("--from must be an ISO 8601 date or datetime") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expression", help="quoted five-field cron expression")
    parser.add_argument("--timezone", default="UTC", metavar="ZONE",
                        help="IANA timezone name (default: UTC)")
    parser.add_argument("--from", dest="from_time", metavar="ISO_TIME",
                        help="start instant; naive values use --timezone")
    parser.add_argument("--count", type=bounded_integer(1, 100), default=5,
                        help="number of occurrences, 1-100 (default: 5)")
    parser.add_argument("--max-years", type=bounded_integer(1, 20), default=5,
                        help="search horizon, 1-20 years (default: 5)")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)
    try:
        zone = ZoneInfo(args.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        parser.error("unknown timezone; use an installed IANA timezone name")
    try:
        schedule = CronSchedule.parse(args.expression)
        start = parse_time(args.from_time, zone)
    except CronError as exc:
        parser.error(str(exc))
    occurrences = schedule.next_occurrences(start, zone, args.count, args.max_years)
    iso_times = [value.isoformat(timespec="minutes") for value in occurrences]
    ok = len(occurrences) == args.count
    if args.json:
        print(json.dumps({
            "ok": ok,
            "expression": args.expression,
            "timezone": args.timezone,
            "from": start.isoformat(timespec="minutes"),
            "occurrences": iso_times,
            "requested_count": args.count,
            "max_years": args.max_years,
        }, separators=(",", ":")))
    elif ok:
        print(f"Expression: {args.expression}")
        print(f"Timezone: {args.timezone}")
        print(f"Next {args.count} occurrence(s):")
        for number, value in enumerate(iso_times, 1):
            print(f"{number}. {value}")
    else:
        print(f"No {args.count} occurrence(s) found within {args.max_years} year(s).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
