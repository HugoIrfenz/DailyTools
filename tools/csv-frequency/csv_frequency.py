#!/usr/bin/env python3
"""Count values in selected CSV columns."""

import argparse
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence


class FrequencyError(ValueError):
    pass


def validate_header(header: Sequence[str]) -> None:
    if not header:
        raise FrequencyError("CSV has no header row")
    if any(name == "" for name in header):
        raise FrequencyError("CSV header contains an empty column name")
    seen = set()
    duplicates = []
    for name in header:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    if duplicates:
        raise FrequencyError("duplicate CSV header: " + ", ".join(repr(x) for x in duplicates))


def analyze(
    rows: Sequence[Sequence[str]],
    header: Sequence[str],
    selected: Sequence[str],
    top: int,
    ignore_empty: bool,
) -> Dict[str, object]:
    validate_header(header)
    names = list(selected) if selected else list(header)
    if len(set(names)) != len(names):
        raise FrequencyError("selected columns must not be repeated")
    missing = [name for name in names if name not in header]
    if missing:
        raise FrequencyError("unknown column: " + ", ".join(repr(x) for x in missing))
    indexes = [header.index(name) for name in names]
    counters = [Counter() for _ in names]
    for row_number, row in enumerate(rows, start=2):
        if len(row) != len(header):
            raise FrequencyError(
                f"row {row_number} has {len(row)} fields; expected {len(header)}"
            )
        for counter, index in zip(counters, indexes):
            value = row[index]
            if value or not ignore_empty:
                counter[value] += 1
    columns = []
    for name, counter in zip(names, counters):
        values = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:top]
        columns.append(
            {
                "name": name,
                "distinct": len(counter),
                "values": [{"value": value, "count": count} for value, count in values],
            }
        )
    return {"rows": len(rows), "columns": columns}


def read_csv(path: str, delimiter: str) -> tuple[List[str], List[List[str]]]:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FrequencyError(f"input is not valid UTF-8 at byte {exc.start}") from exc
    try:
        reader = csv.reader(text.splitlines(keepends=True), delimiter=delimiter, strict=True)
        records = list(reader)
    except csv.Error as exc:
        raise FrequencyError(f"invalid CSV: {exc}") from exc
    if not records:
        raise FrequencyError("CSV is empty")
    return records[0], records[1:]


def render_tsv(result: Dict[str, object]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    for index, column in enumerate(result["columns"]):
        if index:
            writer.writerow([])
        writer.writerow(["column", column["name"], "distinct", column["distinct"]])
        writer.writerow(["count", "value"])
        for item in column["values"]:
            writer.writerow([item["count"], item["value"]])
    return stream.getvalue().rstrip("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Count frequent values in CSV columns.")
    parser.add_argument("input", help="CSV file, or - for stdin")
    parser.add_argument("--column", action="append", default=[], help="column to count; repeatable")
    parser.add_argument("--top", type=int, default=10, help="maximum values per column (default: 10)")
    parser.add_argument("--ignore-empty", action="store_true", help="exclude empty strings")
    parser.add_argument("--delimiter", default=",", help="single-character delimiter")
    parser.add_argument("--tsv", action="store_true", help="write a human-readable TSV summary")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error("--top must be at least 1")
    if len(args.delimiter) != 1 or args.delimiter in '\r\n"':
        parser.error("--delimiter must be one character other than CR, LF, or a quote")
    try:
        header, rows = read_csv(args.input, args.delimiter)
        result = analyze(rows, header, args.column, args.top, args.ignore_empty)
        output = render_tsv(result) if args.tsv else json.dumps(result, ensure_ascii=False, indent=2)
        sys.stdout.write(output + "\n")
    except (FrequencyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
