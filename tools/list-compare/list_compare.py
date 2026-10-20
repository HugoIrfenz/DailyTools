#!/usr/bin/env python3
"""Compare membership of two UTF-8 line lists and emit JSON."""

import argparse
from contextlib import ExitStack
import json
import sys

MAX_INPUT = 16 * 1024 * 1024


def read_values(stream, limit=MAX_INPUT):
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"each input is limited to {limit} bytes")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("input is not valid UTF-8") from exc
    if not text:
        return []
    parts = text.split("\n")
    lines = [part[:-1] if index < len(parts) - 1 and part.endswith("\r") else part
             for index, part in enumerate(parts)]
    if text.endswith("\n"):
        lines.pop()
    return lines


def compare_values(left, right):
    left_unique, right_unique = dict.fromkeys(left), dict.fromkeys(right)
    only_left = [value for value in left_unique if value not in right_unique]
    only_right = [value for value in right_unique if value not in left_unique]
    return {
        "same_membership": not only_left and not only_right,
        "left_lines": len(left), "right_lines": len(right),
        "left_unique": len(left_unique), "right_unique": len(right_unique),
        "only_left": only_left, "only_right": only_right,
        "common": [value for value in left_unique if value in right_unique],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", help="left file or - for stdin")
    parser.add_argument("right", help="right file or - for stdin")
    parser.add_argument("--only", choices=("left", "right", "common"),
                        help="emit only this JSON array instead of the full report")
    args = parser.parse_args(argv)
    if args.left == args.right == "-":
        parser.error("only one input may use stdin")
    try:
        with ExitStack() as stack:
            values = []
            for path in (args.left, args.right):
                stream = (sys.stdin.buffer if path == "-"
                          else stack.enter_context(open(path, "rb")))
                values.append(read_values(stream))
            result = compare_values(*values)
        key = {"left": "only_left", "right": "only_right", "common": "common"}
        output = result[key[args.only]] if args.only else result
        print(json.dumps(output, ensure_ascii=True))
    except (OSError, ValueError) as exc:
        print(f"list-compare: {exc}", file=sys.stderr)
        return 2
    return 0 if result["same_membership"] else 1


if __name__ == "__main__":
    sys.exit(main())
