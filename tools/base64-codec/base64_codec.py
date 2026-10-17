#!/usr/bin/env python3
"""Encode bytes or decode canonical padded Base64, locally."""

import argparse
import base64
import binascii
import re
import sys

MAX_INPUT = 16 * 1024 * 1024
WHITESPACE = b" \t\r\n"


def encode(data, urlsafe=False):
    return base64.urlsafe_b64encode(data) if urlsafe else base64.b64encode(data)


def decode(data, urlsafe=False):
    compact = data.translate(None, WHITESPACE)
    alphabet = rb"[A-Za-z0-9_-]*={0,2}" if urlsafe else rb"[A-Za-z0-9+/]*={0,2}"
    if re.fullmatch(alphabet, compact) is None:
        raise ValueError("invalid character for the selected Base64 alphabet")
    try:
        decoded = base64.b64decode(compact, altchars=b"-_" if urlsafe else None,
                                   validate=True)
    except binascii.Error as exc:
        raise ValueError("invalid Base64 padding or length") from exc
    if encode(decoded, urlsafe) != compact:
        raise ValueError("input is not canonical padded Base64")
    return decoded


def read_limited(stream, limit=MAX_INPUT):
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"input exceeds {limit} bytes")
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode"))
    parser.add_argument("file", nargs="?", default="-", help="file path or - for stdin")
    parser.add_argument("--urlsafe", action="store_true", help="use -_ instead of +/")
    args = parser.parse_args(argv)
    try:
        if args.file == "-":
            data = read_limited(sys.stdin.buffer)
        else:
            with open(args.file, "rb") as stream:
                data = read_limited(stream)
        result = (encode(data, args.urlsafe) + b"\n" if args.operation == "encode"
                  else decode(data, args.urlsafe))
        sys.stdout.buffer.write(result)
        sys.stdout.buffer.flush()
    except (OSError, ValueError) as exc:
        print(f"base64-codec: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
