#!/usr/bin/env python3
"""Compare two CSV files by one or more key columns."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


class CsvDiffError(ValueError):
    pass


def parse_csv(text: str, label: str) -> Tuple[List[str], List[Dict[str, str]]]:
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        headers = reader.fieldnames
        if headers is None:
            raise CsvDiffError(f"{label}: missing header row")
        if any(header == "" for header in headers):
            raise CsvDiffError(f"{label}: empty header name")
        if len(headers) != len(set(headers)):
            raise CsvDiffError(f"{label}: duplicate header name")

        rows: List[Dict[str, str]] = []
        for line_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise CsvDiffError(f"{label}: row {line_number} has the wrong number of fields")
            rows.append(dict(row))
        return list(headers), rows
    except csv.Error as error:
        raise CsvDiffError(f"{label}: invalid CSV: {error}") from error


def index_rows(
    rows: List[Dict[str, str]], keys: Sequence[str], label: str
) -> Dict[Tuple[str, ...], Dict[str, str]]:
    indexed: Dict[Tuple[str, ...], Dict[str, str]] = {}
    for row_number, row in enumerate(rows, start=2):
        identity = tuple(row[key] for key in keys)
        if identity in indexed:
            rendered = ", ".join(f"{key}={value!r}" for key, value in zip(keys, identity))
            raise CsvDiffError(f"{label}: duplicate key at row {row_number}: {rendered}")
        indexed[identity] = row
    return indexed


def compare_csv(before_text: str, after_text: str, keys: Sequence[str]) -> dict:
    if not keys:
        raise CsvDiffError("at least one key column is required")
    if len(keys) != len(set(keys)):
        raise CsvDiffError("key columns must be unique")

    before_headers, before_rows = parse_csv(before_text, "before")
    after_headers, after_rows = parse_csv(after_text, "after")
    if set(before_headers) != set(after_headers):
        missing = sorted(set(before_headers) - set(after_headers))
        added = sorted(set(after_headers) - set(before_headers))
        details = []
        if missing:
            details.append("missing after: " + ", ".join(missing))
        if added:
            details.append("new after: " + ", ".join(added))
        raise CsvDiffError("header sets differ (" + "; ".join(details) + ")")
    missing_keys = [key for key in keys if key not in before_headers]
    if missing_keys:
        raise CsvDiffError("key column not found: " + ", ".join(missing_keys))

    before_index = index_rows(before_rows, keys, "before")
    after_index = index_rows(after_rows, keys, "after")
    before_keys = set(before_index)
    after_keys = set(after_index)

    def key_object(identity: Tuple[str, ...]) -> dict:
        return dict(zip(keys, identity))

    added = [
        {"key": key_object(identity), "row": after_index[identity]}
        for identity in sorted(after_keys - before_keys)
    ]
    removed = [
        {"key": key_object(identity), "row": before_index[identity]}
        for identity in sorted(before_keys - after_keys)
    ]
    changed = []
    compared_columns = [column for column in after_headers if column not in keys]
    for identity in sorted(before_keys & after_keys):
        fields = {}
        for column in compared_columns:
            before_value = before_index[identity][column]
            after_value = after_index[identity][column]
            if before_value != after_value:
                fields[column] = {"before": before_value, "after": after_value}
        if fields:
            changed.append({"key": key_object(identity), "fields": fields})

    return {
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": len(before_keys & after_keys) - len(changed),
        },
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def read_source(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8-sig")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two CSV files by key columns.")
    parser.add_argument("before", help="earlier CSV file, or - for stdin")
    parser.add_argument("after", help="later CSV file, or - for stdin")
    parser.add_argument(
        "--key",
        action="append",
        required=True,
        help="key column; repeat for a composite key",
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit with status 1 when a difference exists",
    )
    args = parser.parse_args(argv)
    if args.before == "-" and args.after == "-":
        parser.error("only one input may use stdin")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        report = compare_csv(
            read_source(args.before),
            read_source(args.after),
            args.key,
        )
    except (OSError, UnicodeError, CsvDiffError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.compact:
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    differences = sum(report["summary"][name] for name in ("added", "removed", "changed"))
    return 1 if args.check and differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
