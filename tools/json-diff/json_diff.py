#!/usr/bin/env python3
"""Compare two JSON documents locally; exit 0 equal, 1 different, 2 error."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys


class InputError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def reject_constant(value):
    raise InputError(f"non-standard JSON number: {value}")


def read_json(path):
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8-sig")
    return json.loads(raw.lstrip("\ufeff"), parse_float=Decimal,
                      object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def encode(value):
    """Serialize JSON with exact decimal numbers and Unicode text."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + encode(v)
                              for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ",".join(encode(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def child_path(path, key):
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def kind(value):
    # Python bool is an int subclass, but JSON true must differ from JSON 1.
    if type(value) is int or isinstance(value, Decimal):
        return "number"
    return type(value).__name__


def compare(before, after, path=""):
    changes = []
    if kind(before) != kind(after):
        return [{"op": "replace", "path": path, "before": before, "after": after}]
    if isinstance(before, dict):
        for key in sorted(before.keys() | after.keys()):
            pointer = child_path(path, key)
            if key not in before:
                changes.append({"op": "add", "path": pointer, "after": after[key]})
            elif key not in after:
                changes.append({"op": "remove", "path": pointer, "before": before[key]})
            else:
                changes.extend(compare(before[key], after[key], pointer))
    elif isinstance(before, list):
        for index in range(min(len(before), len(after))):
            changes.extend(compare(before[index], after[index], child_path(path, index)))
        for index in range(len(after), len(before)):
            changes.append({"op": "remove", "path": child_path(path, index),
                            "before": before[index]})
        for index in range(len(before), len(after)):
            changes.append({"op": "add", "path": child_path(path, index),
                            "after": after[index]})
    elif before != after:
        changes.append({"op": "replace", "path": path, "before": before, "after": after})
    return changes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", help="original JSON file; '-' reads stdin")
    parser.add_argument("after", help="new JSON file; '-' reads stdin")
    parser.add_argument("--json", action="store_true", help="emit a JSON change report")
    args = parser.parse_args(argv)
    if args.before == args.after == "-":
        print("error: only one input can read stdin", file=sys.stderr)
        return 2
    try:
        changes = compare(read_json(args.before), read_json(args.after))
        if args.json:
            print(encode({"equal": not changes, "count": len(changes), "changes": changes}))
        elif not changes:
            print("No differences.")
        else:
            print(f"{len(changes)} difference(s):")
            for change in changes:
                pointer = json.dumps(change["path"], ensure_ascii=False)
                if change["op"] == "replace":
                    detail = encode(change["before"]) + " -> " + encode(change["after"])
                elif change["op"] == "add":
                    detail = encode(change["after"])
                else:
                    detail = encode(change["before"])
                print(f"{change['op'].upper()} {pointer}: {detail}")
        return 1 if changes else 0
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
