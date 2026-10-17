#!/usr/bin/env python3
"""Add signed durations using integer microseconds."""

import argparse
import json
import re
import sys

UNITS = {"d": 86400000000, "h": 3600000000, "m": 60000000,
         "s": 1000000, "ms": 1000, "us": 1}
TERM = re.compile(r"([0-9]+(?:\.[0-9]+)?)(ms|us|d|h|m|s)")


def parse_duration(expression):
    if len(expression) > 4096:
        raise ValueError("duration exceeds 4096 characters")
    text = expression.strip()
    sign = -1 if text.startswith("-") else 1
    if text.startswith(("-", "+")):
        text = text[1:].lstrip()
    if not text:
        raise ValueError("duration must contain a number and unit")
    total, position = 0, 0
    while position < len(text):
        match = TERM.match(text, position)
        if match is None:
            raise ValueError("expected number followed by d, h, m, s, ms or us")
        number, unit = match.groups()
        whole, dot, fraction = number.partition(".")
        denominator = 10 ** len(fraction)
        numerator = int(whole + fraction) * UNITS[unit]
        value, remainder = divmod(numerator, denominator)
        if remainder:
            raise ValueError("each term must resolve to whole microseconds")
        total += value
        position = match.end()
        while position < len(text) and text[position].isspace():
            position += 1
    return sign * total


def normalize(microseconds):
    remaining = abs(microseconds)
    parts = []
    for unit, factor in UNITS.items():
        count, remaining = divmod(remaining, factor)
        if count:
            parts.append(f"{count}{unit}")
    return ("-" if microseconds < 0 else "") + (" ".join(parts) or "0s")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("durations", nargs="+", help="e.g. '1h 30m' or '-15m'")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        total = sum(parse_duration(value) for value in args.durations)
    except ValueError as exc:
        print(f"duration-sum: {exc}", file=sys.stderr)
        return 2
    result = {"microseconds": total, "normalized": normalize(total)}
    print(json.dumps(result) if args.json else result["normalized"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
