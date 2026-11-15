"""Report duplicate object keys in a JSON document."""
import argparse
import json
import sys
from pathlib import Path


class ObjectPairs(list):
    """Distinguish decoded objects from decoded arrays."""


def reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def duplicates(value, path=()):
    if isinstance(value, ObjectPairs):
        seen = set()
        for key, child in value:
            child_path = (*path, key)
            if key in seen:
                yield child_path
            seen.add(key)
            yield from duplicates(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from duplicates(child, (*path, index))


def check(source):
    value = json.loads(source, object_pairs_hook=ObjectPairs,
                       parse_constant=reject_constant, parse_int=str, parse_float=str)
    return list(duplicates(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 JSON file or - for stdin")
    args = parser.parse_args()
    try:
        source = (sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes())
        matches = check(source.decode("utf-8-sig"))
    except (OSError, ValueError, RecursionError) as error:
        parser.exit(2, f"json-key-check: {error}\n")
    for path in matches:
        print(json.dumps(path))
    return int(bool(matches))


if __name__ == "__main__":
    sys.exit(main())
