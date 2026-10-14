#!/usr/bin/env python3
"""Decode a form query string to an ordered JSON list of name/value pairs."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl


def decode(query, max_fields=1000):
    if query.startswith("?"):
        query = query[1:]
    if re.search(r"%(?![0-9a-fA-F]{2})", query):
        raise ValueError("incomplete percent escape")
    if any(ord(c) < 32 or ord(c) == 127 for c in query):
        raise ValueError("raw control characters are unsupported")
    pairs = parse_qsl(query, keep_blank_values=True, encoding="utf-8",
                      errors="strict", max_num_fields=max_fields, separator="&")
    return [{"name": name, "value": value} for name, value in pairs]


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 query file, or '-' for stdin")
    parser.add_argument("--max-fields", type=positive, default=1000)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        # A single terminal newline is accepted for files and shell pipes.
        text = raw.decode("utf-8")
        if text.endswith("\r\n"):
            text = text[:-2]
        elif text.endswith("\n"):
            text = text[:-1]
        pairs = decode(text, args.max_fields)
    except (OSError, ValueError, UnicodeError):
        print("error: unreadable input, invalid UTF-8/query escapes, or field limit exceeded",
              file=sys.stderr)
        return 2
    print(json.dumps(pairs, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
