#!/usr/bin/env python3
"""Convert a header-based CSV stream to JSON Lines."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional, TextIO


class CSVToJSONLError(ValueError):
    """Raised when CSV input cannot be converted unambiguously."""


def validate_delimiter(value: str) -> str:
    if len(value) != 1:
        raise argparse.ArgumentTypeError("delimiter must be exactly one character")
    return value


def validate_header(header: list[str]) -> None:
    empty = [index + 1 for index, name in enumerate(header) if name == ""]
    if empty:
        raise CSVToJSONLError(
            "empty header name at column" + ("s " if len(empty) > 1 else " ")
            + ", ".join(str(index) for index in empty)
        )
    seen: set[str] = set()
    duplicates: list[str] = []
    for name in header:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    if duplicates:
        raise CSVToJSONLError("duplicate header names: " + ", ".join(repr(x) for x in duplicates))


def convert_csv(source: TextIO, destination: TextIO, delimiter: str = ",") -> int:
    """Write one JSON object per CSV data row and return the row count."""
    reader = csv.reader(source, delimiter=delimiter, strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise CSVToJSONLError("input is empty") from exc
    except csv.Error as exc:
        raise CSVToJSONLError(f"invalid CSV header: {exc}") from exc
    validate_header(header)

    count = 0
    try:
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise CSVToJSONLError(
                    f"row {row_number} has {len(row)} fields; expected {len(header)}"
                )
            json.dump(dict(zip(header, row)), destination, ensure_ascii=False, separators=(",", ":"))
            destination.write("\n")
            count += 1
    except csv.Error as exc:
        raise CSVToJSONLError(f"invalid CSV near row {reader.line_num}: {exc}") from exc
    return count


def same_file(input_name: str, output_name: str) -> bool:
    if "-" in (input_name, output_name):
        return False
    return Path(input_name).resolve() == Path(output_name).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 CSV path, or - for stdin")
    parser.add_argument("-o", "--output", default="-", help="JSONL path (default: stdout)")
    parser.add_argument("-d", "--delimiter", default=",", type=validate_delimiter)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if same_file(args.input, args.output):
        print("error: input and output paths must differ", file=sys.stderr)
        return 1

    source: Optional[TextIO] = None
    destination: Optional[TextIO] = None
    try:
        source = sys.stdin if args.input == "-" else open(
            args.input, "r", encoding="utf-8", newline=""
        )
        destination = sys.stdout if args.output == "-" else open(
            args.output, "w", encoding="utf-8", newline=""
        )
        convert_csv(source, destination, args.delimiter)
    except (OSError, UnicodeError, CSVToJSONLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if source is not None and source is not sys.stdin:
            source.close()
        if destination is not None and destination is not sys.stdout:
            destination.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
