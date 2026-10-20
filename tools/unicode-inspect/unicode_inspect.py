#!/usr/bin/env python3
"""Locate selected Unicode control, format and separator characters in UTF-8 text."""

import argparse
from collections import Counter
import json
import sys
import unicodedata

MAX_INPUT = 16 * 1024 * 1024
CATEGORIES = {"Cc", "Cf", "Zl", "Zp", "Zs"}
ALLOWED = {" ", "\t", "\r", "\n"}


def inspect_text(text, limit=100):
    if not 0 <= limit <= 10000:
        raise ValueError("limit must be between 0 and 10000")
    counts, findings = Counter(), []
    line, column, total = 1, 1, 0
    for character in text:
        category = unicodedata.category(character)
        if category in CATEGORIES and character not in ALLOWED:
            codepoint = f"U+{ord(character):04X}"
            counts[codepoint] += 1
            total += 1
            if len(findings) < limit:
                findings.append({"line": line, "column": column, "codepoint": codepoint,
                                 "category": category,
                                 "name": unicodedata.name(character, "<unnamed>")})
        if character == "\n":
            line, column = line + 1, 1
        else:
            column += 1
    return {"unicode_version": unicodedata.unidata_version,
            "total": total, "shown": len(findings), "omitted": total - len(findings),
            "counts": dict(sorted(counts.items())), "findings": findings}


def read_text(stream, limit=MAX_INPUT):
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"input exceeds {limit} bytes")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("input is not valid UTF-8") from exc


def limit_value(value):
    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be an integer") from exc
    if not 0 <= count <= 10000:
        raise argparse.ArgumentTypeError("limit must be between 0 and 10000")
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="UTF-8 file or - for stdin")
    parser.add_argument("--limit", type=limit_value, default=100,
                        help="maximum individual findings (0..10000; default 100)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.file == "-":
            text = read_text(sys.stdin.buffer)
        else:
            with open(args.file, "rb") as stream:
                text = read_text(stream)
        result = inspect_text(text, args.limit)
        if args.json:
            print(json.dumps(result, ensure_ascii=True))
        else:
            print(f"Matches: {result['total']} (Unicode {result['unicode_version']})")
            for item in result["findings"]:
                print(f"{item['line']}:{item['column']} {item['codepoint']} "
                      f"{item['category']} {item['name']}")
            if result["omitted"]:
                print(f"Omitted: {result['omitted']}")
    except (OSError, ValueError) as exc:
        print(f"unicode-inspect: {exc}", file=sys.stderr)
        return 2
    return 1 if result["total"] else 0


if __name__ == "__main__":
    sys.exit(main())
