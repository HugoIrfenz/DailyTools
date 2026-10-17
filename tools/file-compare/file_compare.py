#!/usr/bin/env python3
"""Report the first byte offset at which two regular files differ."""

import argparse
import json
import os
import stat
import sys
from contextlib import ExitStack

CHUNK_SIZE = 1024 * 1024


def compare_streams(left, right, chunk_size=CHUNK_SIZE):
    if chunk_size < 1:
        raise ValueError("chunk size must be positive")
    offset = 0
    while True:
        a, b = left.read(chunk_size), right.read(chunk_size)
        if a != b:
            for index, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    return offset + index
            return offset + min(len(a), len(b))
        if not a:
            return None
        offset += len(a)


def compare_files(left, right):
    with ExitStack() as stack:
        files = []
        for path in (left, right):
            # Reject named pipes before opening; recheck the opened descriptor.
            if not stat.S_ISREG(os.stat(path).st_mode):
                raise ValueError("inputs must be regular files")
            stream = stack.enter_context(open(path, "rb"))
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("inputs must be regular files")
            files.append(stream)
        sizes = [os.fstat(stream.fileno()).st_size for stream in files]
        offset = compare_streams(*files)
    return {"equal": offset is None, "first_difference": offset,
            "left_bytes": sizes[0], "right_bytes": sizes[1]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = compare_files(args.left, args.right)
    except (OSError, ValueError) as exc:
        print(f"file-compare: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result))
    elif result["equal"]:
        print(f"Equal ({result['left_bytes']} bytes)")
    else:
        print(f"Different at byte offset {result['first_difference']} "
              f"(sizes: {result['left_bytes']}, {result['right_bytes']})")
    return 0 if result["equal"] else 1


if __name__ == "__main__":
    sys.exit(main())
