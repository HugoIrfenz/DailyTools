#!/usr/bin/env python3
"""Parse an exact byte quantity and display decimal and binary sizes."""

import argparse
import json
import re
import sys

DECIMAL = ("B", "kB", "MB", "GB", "TB", "PB", "EB")
BINARY = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
FACTORS = {unit: 1000 ** power for power, unit in enumerate(DECIMAL)}
FACTORS.update({unit: 1024 ** power for power, unit in enumerate(BINARY)})
FACTORS["KB"] = 1000
QUANTITY = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(B|kB|KB|MB|GB|TB|PB|EB|KiB|MiB|GiB|TiB|PiB|EiB)?")


def parse_size(value):
    if len(value) > 256:
        raise ValueError("quantity exceeds 256 characters")
    match = QUANTITY.fullmatch(value.strip())
    if match is None:
        raise ValueError("expected a nonnegative number and a supported byte unit")
    number, unit = match.groups()
    whole, _, fraction = number.partition(".")
    numerator = int(whole + fraction) * FACTORS[unit or "B"]
    count, remainder = divmod(numerator, 10 ** len(fraction))
    if remainder:
        raise ValueError("quantity must resolve to a whole number of bytes")
    return count


def human_size(count, binary=False):
    if count < 0:
        raise ValueError("byte count must be nonnegative")
    units, base = (BINARY, 1024) if binary else (DECIMAL, 1000)
    power = 0
    while power < len(units) - 1 and count >= base ** (power + 1):
        power += 1
    if power == 0:
        return f"{count} B"
    factor = base ** power
    hundredths, remainder = divmod(count * 100, factor)
    if remainder * 2 >= factor:
        hundredths += 1
    return f"{hundredths // 100}.{hundredths % 100:02d} {units[power]}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quantity", help="e.g. '1.5 GiB', '500 MB' or '1024'")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        count = parse_size(args.quantity)
    except ValueError as exc:
        print(f"byte-size: {exc}", file=sys.stderr)
        return 2
    result = {"bytes": count, "decimal": human_size(count),
              "binary": human_size(count, binary=True)}
    if args.json:
        print(json.dumps(result))
    else:
        print(f"{result['bytes']} bytes | {result['decimal']} | {result['binary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
