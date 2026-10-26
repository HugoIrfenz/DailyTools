#!/usr/bin/env python3
"""Select a deterministic reservoir sample of lines from a byte stream."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import BinaryIO, Optional


class LineSampleError(ValueError):
    """Raised when line sampling cannot be performed."""


def positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("count must be an integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("count must be at least 1")
    return number


def sample_lines(source: BinaryIO, count: int, seed: str) -> tuple[list[tuple[int, bytes]], int]:
    generator = random.Random(seed)
    reservoir: list[tuple[int, bytes]] = []
    total = 0
    for total, line in enumerate(source, start=1):
        item = (total, line)
        if len(reservoir) < count:
            reservoir.append(item)
        else:
            slot = generator.randrange(total)
            if slot < count:
                reservoir[slot] = item
    reservoir.sort(key=lambda item: item[0])
    return reservoir, total


def same_file(input_name: str, output_name: str) -> bool:
    if "-" in (input_name, output_name):
        return False
    return Path(input_name).resolve() == Path(output_name).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="input path, or - for stdin")
    parser.add_argument("-n", "--count", type=positive_integer, required=True)
    parser.add_argument("--seed", default="0", help="deterministic seed (default: 0)")
    parser.add_argument("--shuffle", action="store_true", help="shuffle selected lines instead of retaining source order")
    parser.add_argument("-o", "--output", default="-", help="output path (default: stdout)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if same_file(args.input, args.output):
        print("error: input and output paths must differ", file=sys.stderr)
        return 1

    source: Optional[BinaryIO] = None
    output: Optional[BinaryIO] = None
    try:
        source = sys.stdin.buffer if args.input == "-" else open(args.input, "rb")
        selected, _ = sample_lines(source, args.count, args.seed)
        if args.shuffle:
            random.Random(args.seed + ":output").shuffle(selected)
        output = sys.stdout.buffer if args.output == "-" else open(args.output, "wb")
        for _, line in selected:
            output.write(line)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if source is not None and source is not sys.stdin.buffer:
            source.close()
        if output is not None and output is not sys.stdout.buffer:
            output.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
