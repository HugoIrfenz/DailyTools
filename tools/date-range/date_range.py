"""Print calendar dates in an inclusive range."""
import argparse
from datetime import date


def parse_date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value:
            return parsed
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("expected a valid YYYY-MM-DD date")


def dates(start, end, weekdays_only=False):
    for ordinal in range(start.toordinal(), end.toordinal() + 1):
        day = date.fromordinal(ordinal)
        if not weekdays_only or day.weekday() < 5:
            yield day.isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=parse_date)
    parser.add_argument("end", type=parse_date)
    parser.add_argument("--weekdays", action="store_true", help="include Monday through Friday only")
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("end must be on or after start")
    for day in dates(args.start, args.end, args.weekdays):
        print(day)


if __name__ == "__main__":
    main()
