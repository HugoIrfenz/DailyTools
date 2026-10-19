#!/usr/bin/env python3
"""Convert explicitly selected text encodings, writing bytes to stdout."""

import argparse
import codecs
import sys

MAX_INPUT = 16 * 1024 * 1024
OUTPUT_ENCODINGS = ("utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "ascii")
INPUT_ENCODINGS = OUTPUT_ENCODINGS + ("utf-16",)


def transcode(data, source, target):
    if source not in INPUT_ENCODINGS or target not in OUTPUT_ENCODINGS:
        raise ValueError("unsupported encoding")
    try:
        decoder = codecs.getincrementaldecoder(source)(errors="strict")
        text = decoder.decode(data, final=True)
    except UnicodeError as exc:
        raise ValueError(f"input is not valid {source}") from exc
    try:
        return text.encode(target, errors="strict")
    except UnicodeError as exc:
        raise ValueError(f"text cannot be represented as {target}") from exc


def read_limited(stream, limit=MAX_INPUT):
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"input exceeds {limit} bytes")
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="input file or - for stdin")
    parser.add_argument("--from", dest="source", required=True, choices=INPUT_ENCODINGS)
    parser.add_argument("--to", dest="target", required=True, choices=OUTPUT_ENCODINGS)
    args = parser.parse_args(argv)
    try:
        if args.file == "-":
            data = read_limited(sys.stdin.buffer)
        else:
            with open(args.file, "rb") as stream:
                data = read_limited(stream)
        result = transcode(data, args.source, args.target)
        sys.stdout.buffer.write(result)
        sys.stdout.buffer.flush()
    except (OSError, ValueError) as exc:
        print(f"text-transcode: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
