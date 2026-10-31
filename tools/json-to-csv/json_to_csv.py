#!/usr/bin/env python3
"""Convert an array of flat JSON objects to CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Optional, TextIO


class JsonToCsvError(ValueError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JsonToCsvError(f"duplicate object key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise JsonToCsvError(f"non-standard JSON number: {value}")


def read_json(path: str) -> Any:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
    )


def validate_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise JsonToCsvError("top-level JSON value must be an array")
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise JsonToCsvError(f"item {index} must be an object")
    return value


def infer_fields(rows: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    return fields


def scalar_text(value: Any, row_number: int, field: str) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        try:
            return json.dumps(value, ensure_ascii=False, allow_nan=False)
        except ValueError as exc:
            raise JsonToCsvError(f"item {row_number} field {field!r} is not finite") from exc
    raise JsonToCsvError(f"item {row_number} field {field!r} is not a scalar")


def convert_rows(
    rows: list[dict[str, Any]], fields: Optional[list[str]] = None
) -> tuple[list[str], list[list[str]]]:
    selected = list(fields) if fields is not None else infer_fields(rows)
    if len(set(selected)) != len(selected):
        raise JsonToCsvError("field names must be unique")
    if not selected:
        raise JsonToCsvError("no fields available; use --field for an empty array")
    output: list[list[str]] = []
    for row_number, row in enumerate(rows):
        output.append(
            [scalar_text(row.get(field), row_number, field) for field in selected]
        )
    return selected, output


def one_character(value: str) -> str:
    if len(value) != 1:
        raise argparse.ArgumentTypeError("delimiter must be one character")
    return value


def write_csv(
    stream: TextIO, fields: list[str], rows: list[list[str]], delimiter: str
) -> None:
    writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
    writer.writerow(fields)
    writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert flat JSON objects to CSV.")
    parser.add_argument("input", nargs="?", default="-", help="JSON file or - for stdin")
    parser.add_argument(
        "--field", action="append", dest="fields", help="output field; repeat to set order"
    )
    parser.add_argument("--delimiter", type=one_character, default=",")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = validate_rows(read_json(args.input))
        fields, output = convert_rows(rows, args.fields)
        write_csv(sys.stdout, fields, output, args.delimiter)
    except (OSError, UnicodeError, json.JSONDecodeError, JsonToCsvError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
