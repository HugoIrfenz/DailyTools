#!/usr/bin/env python3
"""Convert a JSON array to JSON Lines, retaining decimal number values."""
import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("non-standard number: " + value)


def parse_decimal(value):
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("decimal number exceeds runtime limits") from exc


def encode(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(encode(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=True) + ":" + encode(v)
                              for k, v in value.items()) + "}"
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


def convert(text):
    values = json.loads(text, object_pairs_hook=unique_object,
                        parse_float=parse_decimal, parse_constant=reject_constant)
    if not isinstance(values, list):
        raise ValueError("top-level JSON must be an array")
    return "".join(encode(value) + "\n" for value in values)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        output = convert(data.decode("utf-8-sig"))
        sys.stdout.write(output)
    except BrokenPipeError:
        return 0
    except (OSError, ValueError, RecursionError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
