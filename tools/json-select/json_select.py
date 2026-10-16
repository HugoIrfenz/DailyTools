#!/usr/bin/env python3
"""Select a JSON value using an array of object keys and array indexes."""

import argparse
from decimal import Decimal, DecimalException
import json
from pathlib import Path
import sys


class MissingPath(Exception):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("non-JSON numeric constant")


def parse_document(raw):
    return json.loads(raw.decode("utf-8"), parse_int=Decimal, parse_float=Decimal,
                      object_pairs_hook=unique_object, parse_constant=reject_constant)


def parse_path(raw):
    path = json.loads(raw)
    if not isinstance(path, list):
        raise ValueError("path must be an array")
    for part in path:
        if not (isinstance(part, str) or (type(part) is int and part >= 0)):
            raise ValueError("path elements must be strings or non-negative integers")
    return path


def select(document, path):
    value = document
    for number, part in enumerate(path, 1):
        if isinstance(value, dict) and isinstance(part, str) and part in value:
            value = value[part]
        elif isinstance(value, list) and type(part) is int and 0 <= part < len(value):
            value = value[part]
        else:
            raise MissingPath(f"path not found at segment {number}")
    return value


def encode(value):
    """Encode Decimal numbers as JSON numbers, without converting through float."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite number")
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, list):
        return "[" + ",".join(encode(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(key, ensure_ascii=True) + ":" + encode(item)
                              for key, item in value.items()) + "}"
    raise ValueError("unsupported value")


def positive(raw):
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 JSON file, or '-' for stdin")
    parser.add_argument("path", help='JSON array, for example ["users",0,"name"]; [] selects the root')
    parser.add_argument("--max-bytes", type=positive, default=16 * 1024 * 1024,
                        help="input byte limit (default: 16777216)")
    args = parser.parse_args(argv)
    try:
        path = parse_path(args.path)
    except (ValueError, RecursionError):
        parser.error("path must be a JSON array of string keys and non-negative integer indexes")
    try:
        if args.input == "-":
            raw = sys.stdin.buffer.read(args.max_bytes + 1)
        else:
            with Path(args.input).open("rb") as handle:
                raw = handle.read(args.max_bytes + 1)
        if len(raw) > args.max_bytes:
            raise ValueError("input limit exceeded")
        document = parse_document(raw)
        output = encode(select(document, path))
    except MissingPath as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError, UnicodeError, DecimalException, RecursionError, OverflowError):
        print("error: unreadable/invalid JSON, input limit, or parser limit exceeded", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
