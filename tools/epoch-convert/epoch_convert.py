#!/usr/bin/env python3
"""Convert decimal Unix timestamps and offset-aware ISO datetimes."""

import argparse
from datetime import datetime, timedelta, timezone
import json
import re
import sys

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
NUMBER = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?\Z")
ISO = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                 r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z")


def parse_epoch(value, unit="seconds"):
    if not NUMBER.fullmatch(value):
        raise ValueError("use a decimal timestamp, not scientific notation")
    width = 6 if unit == "seconds" else 3
    sign = -1 if value.startswith("-") else 1
    unsigned = value.lstrip("+-")
    whole, dot, fraction = unsigned.partition(".")
    if len(fraction) > width:
        raise ValueError("timestamp exceeds microsecond precision")
    micros = sign * (int(whole) * 10**width + int(fraction.ljust(width, "0")))
    return EPOCH + timedelta(microseconds=micros)


def parse_iso(value):
    if not ISO.fullmatch(value):
        raise ValueError("use YYYY-MM-DDTHH:MM:SS[.fraction] with Z or +/-HH:MM")
    value = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def decimal_string(micros, width):
    whole, fraction = divmod(abs(micros), 10**width)
    suffix = f"{fraction:0{width}d}".rstrip("0")
    return ("-" if micros < 0 else "") + str(whole) + ("." + suffix if suffix else "")


def report(value):
    value = value.astimezone(timezone.utc)
    delta = value - EPOCH
    micros = (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds
    return {"utc": value.isoformat(timespec="microseconds"),
            "seconds": decimal_string(micros, 6),
            "milliseconds": decimal_string(micros, 3)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    from_epoch = commands.add_parser("from-epoch")
    from_epoch.add_argument("value", help="decimal Unix timestamp")
    from_epoch.add_argument("--unit", choices=("seconds", "milliseconds"), default="seconds")
    from_epoch.add_argument("--json", action="store_true")
    to_epoch = commands.add_parser("to-epoch")
    to_epoch.add_argument("value", help="offset-aware ISO datetime")
    to_epoch.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = parse_epoch(args.value, args.unit) if args.command == "from-epoch" else parse_iso(args.value)
        result = report(value)
    except (ValueError, OverflowError):
        parser.error("invalid time, unsupported precision/format, or date outside years 1-9999")
    if args.json:
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(f"UTC: {result['utc']}")
        print(f"Seconds: {result['seconds']}")
        print(f"Milliseconds: {result['milliseconds']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
