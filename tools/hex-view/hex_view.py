#!/usr/bin/env python3
"""Render binary input as offsets, hexadecimal bytes, and ASCII."""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path
from typing import BinaryIO, Iterator, Optional


def non_negative_int(value: str) -> int:
    try:
        number = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value}") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return number


def width_int(value: str) -> int:
    number = non_negative_int(value)
    if not 1 <= number <= 64:
        raise argparse.ArgumentTypeError("width must be between 1 and 64")
    return number


def skip_bytes(stream: BinaryIO, count: int) -> None:
    if count == 0:
        return
    try:
        stream.seek(count, 1)
        return
    except (OSError, AttributeError):
        pass

    remaining = count
    while remaining:
        chunk = stream.read(min(remaining, 64 * 1024))
        if not chunk:
            break
        remaining -= len(chunk)


def iter_chunks(
    stream: BinaryIO, *, offset: int = 0, length: Optional[int] = None, width: int = 16
) -> Iterator[tuple[int, bytes]]:
    skip_bytes(stream, offset)
    position = offset
    remaining = length
    while remaining is None or remaining > 0:
        size = width if remaining is None else min(width, remaining)
        chunk = stream.read(size)
        if not chunk:
            return
        yield position, chunk
        position += len(chunk)
        if remaining is not None:
            remaining -= len(chunk)


def format_line(offset: int, data: bytes, width: int = 16) -> str:
    address_width = max(8, len(f"{offset:x}"))
    hex_part = " ".join(f"{byte:02x}" for byte in data)
    hex_part = hex_part.ljust(width * 3 - 1)
    ascii_part = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in data)
    return f"{offset:0{address_width}x}  {hex_part}  |{ascii_part}|"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Display bytes as hex and printable ASCII.")
    parser.add_argument("input", nargs="?", default="-", help="file or - for stdin")
    parser.add_argument("--offset", type=non_negative_int, default=0, help="starting byte offset")
    parser.add_argument("--length", type=non_negative_int, help="maximum bytes to display")
    parser.add_argument("--width", type=width_int, default=16, help="bytes per line (1-64)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manager = contextlib.nullcontext(sys.stdin.buffer) if args.input == "-" else open(Path(args.input), "rb")
        with manager as stream:
            for offset, data in iter_chunks(
                stream, offset=args.offset, length=args.length, width=args.width
            ):
                print(format_line(offset, data, args.width))
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
