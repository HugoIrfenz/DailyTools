#!/usr/bin/env python3
"""Convert JSON Lines records into one JSON array."""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple


class ConvertError(ValueError):
    pass


def unique_object(pairs: Iterable[Tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConvertError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ConvertError("non-finite number")
    return number


def reject_constant(value: str) -> None:
    raise ConvertError(f"non-standard number {value}")


def parse_lines(text: str, reject_blank: bool) -> List[Any]:
    records: List[Any] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            if reject_blank:
                raise ConvertError(f"blank line at line {line_number}")
            continue
        try:
            value = json.loads(
                line,
                object_pairs_hook=unique_object,
                parse_float=finite_float,
                parse_constant=reject_constant,
            )
        except json.JSONDecodeError as exc:
            raise ConvertError(
                f"invalid JSON at line {line_number}, column {exc.colno}: {exc.msg}"
            ) from exc
        except ConvertError as exc:
            raise ConvertError(f"line {line_number}: {exc}") from exc
        records.append(value)
    return records


def read_text(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConvertError(f"input is not valid UTF-8 at byte {exc.start}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert JSON Lines into one JSON array.")
    parser.add_argument("input", help="JSONL file, or - for stdin")
    parser.add_argument("--indent", type=int, help="indentation width; default is compact")
    parser.add_argument("--reject-blank", action="store_true", help="reject blank lines instead of ignoring them")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.indent is not None and not 0 <= args.indent <= 16:
        parser.error("--indent must be between 0 and 16")
    try:
        records = parse_lines(read_text(args.input), args.reject_blank)
        separators = (",", ":") if args.indent is None else (",", ": ")
        output = json.dumps(
            records, ensure_ascii=False, allow_nan=False,
            indent=args.indent, separators=separators,
        )
        sys.stdout.write(output + "\n")
    except (ConvertError, OSError, UnicodeEncodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
