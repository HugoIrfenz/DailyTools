#!/usr/bin/env python3
"""Select and reorder columns from a CSV file."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, Optional, TextIO


class CSVSelectError(ValueError):
    """Raised when CSV input cannot be selected unambiguously."""


def validate_delimiter(value: str) -> str:
    if len(value) != 1:
        raise argparse.ArgumentTypeError("delimiter must be exactly one character")
    return value


def selected_indexes(header: list[str], columns: Iterable[str]) -> list[int]:
    duplicates = sorted({name for name in header if header.count(name) > 1})
    if duplicates:
        raise CSVSelectError("duplicate header names: " + ", ".join(repr(x) for x in duplicates))

    requested = list(columns)
    if len(set(requested)) != len(requested):
        raise CSVSelectError("requested column names must be unique")

    lookup = {name: index for index, name in enumerate(header)}
    missing = [name for name in requested if name not in lookup]
    if missing:
        raise CSVSelectError("missing columns: " + ", ".join(repr(x) for x in missing))
    return [lookup[name] for name in requested]


def select_csv(
    source: TextIO,
    destination: TextIO,
    columns: Iterable[str],
    delimiter: str = ",",
    output_delimiter: Optional[str] = None,
) -> int:
    """Write selected columns and return the number of data rows."""
    reader = csv.reader(source, delimiter=delimiter, strict=True)
    writer = csv.writer(
        destination,
        delimiter=output_delimiter or delimiter,
        lineterminator="\n",
    )

    try:
        header = next(reader)
    except StopIteration as exc:
        raise CSVSelectError("input is empty") from exc
    except csv.Error as exc:
        raise CSVSelectError(f"invalid CSV header: {exc}") from exc

    names = list(columns)
    indexes = selected_indexes(header, names)
    writer.writerow(names)

    count = 0
    try:
        for line_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise CSVSelectError(
                    f"row {line_number} has {len(row)} fields; expected {len(header)}"
                )
            writer.writerow([row[index] for index in indexes])
            count += 1
    except csv.Error as exc:
        raise CSVSelectError(f"invalid CSV near row {reader.line_num}: {exc}") from exc
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 CSV path, or - for stdin")
    parser.add_argument("columns", nargs="+", help="header names in output order")
    parser.add_argument("-o", "--output", default="-", help="output path (default: stdout)")
    parser.add_argument(
        "-d", "--delimiter", default=",", type=validate_delimiter, help="input delimiter"
    )
    parser.add_argument(
        "--output-delimiter",
        type=validate_delimiter,
        help="output delimiter (default: same as input)",
    )
    return parser


def same_file(input_name: str, output_name: str) -> bool:
    if "-" in (input_name, output_name):
        return False
    return Path(input_name).resolve() == Path(output_name).resolve()


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
        select_csv(
            source,
            destination,
            args.columns,
            delimiter=args.delimiter,
            output_delimiter=args.output_delimiter,
        )
    except (OSError, UnicodeError, CSVSelectError) as exc:
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
