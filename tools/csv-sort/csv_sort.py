#!/usr/bin/env python3
"""Sort header-based CSV rows by named columns."""

import argparse
import csv
import io
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


class SortError(ValueError):
    pass


def validate_header(header: Sequence[str]) -> None:
    if not header:
        raise SortError("CSV has no header row")
    if any(name == "" for name in header):
        raise SortError("CSV header contains an empty column name")
    seen = set()
    duplicates = []
    for name in header:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    if duplicates:
        raise SortError("duplicate CSV header: " + ", ".join(repr(x) for x in duplicates))


def sort_rows(
    header: Sequence[str],
    rows: Sequence[Sequence[str]],
    keys: Sequence[str],
    numeric: bool,
    ignore_case: bool,
    reverse: bool,
) -> List[List[str]]:
    validate_header(header)
    if len(set(keys)) != len(keys):
        raise SortError("sort keys must not be repeated")
    missing = [name for name in keys if name not in header]
    if missing:
        raise SortError("unknown sort key: " + ", ".join(repr(x) for x in missing))
    indexes = [header.index(name) for name in keys]
    decorated: List[Tuple[Tuple[object, ...], List[str]]] = []
    for row_number, source_row in enumerate(rows, start=2):
        row = list(source_row)
        if len(row) != len(header):
            raise SortError(
                f"row {row_number} has {len(row)} fields; expected {len(header)}"
            )
        values: List[object] = []
        for name, index in zip(keys, indexes):
            value = row[index]
            if numeric:
                try:
                    number = Decimal(value)
                except InvalidOperation as exc:
                    raise SortError(
                        f"row {row_number} has a non-numeric value in column {name!r}"
                    ) from exc
                if not number.is_finite():
                    raise SortError(
                        f"row {row_number} has a non-finite value in column {name!r}"
                    )
                values.append(number)
            else:
                values.append(value.casefold() if ignore_case else value)
        decorated.append((tuple(values), row))
    decorated.sort(key=lambda item: item[0], reverse=reverse)
    return [row for _, row in decorated]


def read_csv(path: str, delimiter: str) -> Tuple[List[str], List[List[str]]]:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SortError(f"input is not valid UTF-8 at byte {exc.start}") from exc
    try:
        records = list(csv.reader(text.splitlines(keepends=True), delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise SortError(f"invalid CSV: {exc}") from exc
    if not records:
        raise SortError("CSV is empty")
    return records[0], records[1:]


def render_csv(header: Sequence[str], rows: Sequence[Sequence[str]], delimiter: str) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sort CSV rows by one or more named columns.")
    parser.add_argument("input", help="CSV file, or - for stdin")
    parser.add_argument("--key", action="append", required=True, help="sort column; repeatable")
    parser.add_argument("--numeric", action="store_true", help="compare every key as a finite decimal")
    parser.add_argument("--ignore-case", action="store_true", help="case-fold text keys")
    parser.add_argument("--reverse", action="store_true", help="sort all keys in descending order")
    parser.add_argument("--delimiter", default=",", help="single-character delimiter")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if len(args.delimiter) != 1 or args.delimiter in '\r\n"':
        parser.error("--delimiter must be one character other than CR, LF, or a quote")
    if args.numeric and args.ignore_case:
        parser.error("--ignore-case cannot be combined with --numeric")
    try:
        header, rows = read_csv(args.input, args.delimiter)
        ordered = sort_rows(
            header, rows, args.key, args.numeric, args.ignore_case, args.reverse
        )
        sys.stdout.write(render_csv(header, ordered, args.delimiter))
    except (SortError, OSError, UnicodeEncodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
