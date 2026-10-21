#!/usr/bin/env python3
"""Decode JSON header and payload from a three-segment compact token."""

import argparse
import base64
import binascii
import json
import math
import sys

MAX_INPUT = 64 * 1024
ALPHABET = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")


def decode_segment(segment, label, allow_empty=False):
    if not segment and not allow_empty:
        raise ValueError(f"{label} segment is empty")
    if any(byte not in ALPHABET for byte in segment):
        raise ValueError(f"{label} contains invalid base64url characters")
    padding = b"=" * (-len(segment) % 4)
    try:
        decoded = base64.b64decode(segment + padding, altchars=b"-_", validate=True)
    except binascii.Error as exc:
        raise ValueError(f"{label} is not valid unpadded base64url") from exc
    if base64.urlsafe_b64encode(decoded).rstrip(b"=") != segment:
        raise ValueError(f"{label} is not canonical unpadded base64url")
    return decoded


def json_object(data, label):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} is not UTF-8") from exc

    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"{label} contains duplicate JSON keys")
            result[key] = value
        return result

    def constant(_value):
        raise ValueError(f"{label} contains a non-finite JSON number")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{label} contains a non-finite JSON number")
        return number

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant,
                           parse_float=finite_float)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def inspect_token(data):
    token = data.strip(b" \t\r\n")
    if not token:
        raise ValueError("token is empty")
    parts = token.split(b".")
    if len(parts) != 3:
        raise ValueError("token must contain exactly three dot-separated segments")
    header_bytes = decode_segment(parts[0], "header")
    payload_bytes = decode_segment(parts[1], "payload")
    signature = decode_segment(parts[2], "signature", allow_empty=True)
    return {"header": json_object(header_bytes, "header"),
            "payload": json_object(payload_bytes, "payload"),
            "signature_bytes": len(signature), "signature_present": bool(signature)}


def read_limited(stream, limit=MAX_INPUT):
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"input exceeds {limit} bytes")
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="token file or - for stdin")
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args(argv)
    try:
        if args.file == "-":
            data = read_limited(sys.stdin.buffer)
        else:
            with open(args.file, "rb") as stream:
                data = read_limited(stream)
        result = inspect_token(data)
        print(json.dumps(result, ensure_ascii=True, indent=2 if args.pretty else None,
                         separators=None if args.pretty else (",", ":")))
    except (OSError, ValueError) as exc:
        print(f"jwt-inspect: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
