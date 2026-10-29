#!/usr/bin/env python3
"""Join two CSV files by named key columns."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional, TextIO


class CsvJoinError(ValueError):
    pass


def read_table(path: Path, delimiter: str = ",") -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter=delimiter)
        header = next(reader, None)
        if header is None:
            raise CsvJoinError(f"{path}: empty CSV")
        if len(set(header)) != len(header):
            raise CsvJoinError(f"{path}: duplicate header names")
        rows: list[list[str]] = []
        for line, row in enumerate(reader, 2):
            if len(row) != len(header):
                raise CsvJoinError(
                    f"{path}:{line}: expected {len(header)} columns, found {len(row)}"
                )
            rows.append(row)
    return header, rows


def output_header(left: list[str], right: list[str], right_key: str) -> list[str]:
    result = list(left)
    used = set(result)
    for name in right:
        if name == right_key:
            continue
        candidate = name if name not in used else f"right.{name}"
        suffix = 2
        while candidate in used:
            candidate = f"right{suffix}.{name}"
            suffix += 1
        result.append(candidate)
        used.add(candidate)
    return result


def join_rows(
    left_header: list[str],
    left_rows: list[list[str]],
    right_header: list[str],
    right_rows: list[list[str]],
    left_key: str,
    right_key: str,
    how: str,
) -> tuple[list[str], list[list[str]]]:
    if left_key not in left_header:
        raise CsvJoinError(f"left key not found: {left_key}")
    if right_key not in right_header:
        raise CsvJoinError(f"right key not found: {right_key}")
    left_index = left_header.index(left_key)
    right_index = right_header.index(right_key)
    right_value_indexes = [i for i, name in enumerate(right_header) if name != right_key]
    index: dict[str, list[tuple[int, list[str]]]] = defaultdict(list)
    for row_number, row in enumerate(right_rows):
        index[row[right_index]].append((row_number, row))

    joined: list[list[str]] = []
    matched_right: set[int] = set()
    for left_row in left_rows:
        matches = index.get(left_row[left_index], [])
        if matches:
            for row_number, right_row in matches:
                matched_right.add(row_number)
                joined.append(left_row + [right_row[i] for i in right_value_indexes])
        elif how in ("left", "full"):
            joined.append(left_row + [""] * len(right_value_indexes))

    if how == "full":
        for row_number, right_row in enumerate(right_rows):
            if row_number in matched_right:
                continue
            left_blank = [""] * len(left_header)
            left_blank[left_index] = right_row[right_index]
            joined.append(left_blank + [right_row[i] for i in right_value_indexes])
    return output_header(left_header, right_header, right_key), joined


def one_character(value: str) -> str:
    if len(value) != 1:
        raise argparse.ArgumentTypeError("delimiter must be one character")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Join two CSV files by named keys.")
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--left-key", required=True)
    parser.add_argument("--right-key", help="defaults to --left-key")
    parser.add_argument("--how", choices=("inner", "left", "full"), default="inner")
    parser.add_argument("--delimiter", type=one_character, default=",")
    return parser


def write_csv(stream: TextIO, header: list[str], rows: list[list[str]], delimiter: str) -> None:
    writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    right_key = args.right_key or args.left_key
    try:
        left_header, left_rows = read_table(args.left, args.delimiter)
        right_header, right_rows = read_table(args.right, args.delimiter)
        header, rows = join_rows(
            left_header,
            left_rows,
            right_header,
            right_rows,
            args.left_key,
            right_key,
            args.how,
        )
        write_csv(sys.stdout, header, rows, args.delimiter)
    except (OSError, UnicodeError, csv.Error, CsvJoinError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
