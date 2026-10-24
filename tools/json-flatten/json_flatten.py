#!/usr/bin/env python3
"""Flatten JSON leaves into JSON Pointer and value records."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterator, Optional, TextIO


class JSONFlattenError(ValueError):
    """Raised when JSON input is invalid or ambiguous."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JSONFlattenError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise JSONFlattenError(f"non-standard JSON number: {value}")


def load_json(stream: TextIO, source_name: str) -> Any:
    try:
        return json.load(
            stream,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except JSONFlattenError:
        raise
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise JSONFlattenError(f"invalid JSON in {source_name}: {exc}") from exc


def escape_token(token: str) -> str:
    """Escape one JSON Pointer reference token."""
    return token.replace("~", "~0").replace("/", "~1")


def flatten(value: Any) -> Iterator[dict[str, Any]]:
    """Yield leaf records in source order without recursive calls."""
    stack: list[tuple[str, Any]] = [("", value)]
    while stack:
        pointer, current = stack.pop()
        if isinstance(current, dict) and current:
            for key, child in reversed(list(current.items())):
                stack.append((pointer + "/" + escape_token(key), child))
        elif isinstance(current, list) and current:
            for index in range(len(current) - 1, -1, -1):
                stack.append((pointer + "/" + str(index), current[index]))
        else:
            yield {"path": pointer, "value": current}


def write_records(records: Iterator[dict[str, Any]], output: TextIO, array: bool) -> int:
    count = 0
    if array:
        materialized = list(records)
        json.dump(materialized, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        return len(materialized)

    for record in records:
        json.dump(record, output, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        output.write("\n")
        count += 1
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 JSON path, or - for stdin")
    parser.add_argument("-o", "--output", default="-", help="output path (default: stdout)")
    parser.add_argument("--array", action="store_true", help="write one JSON array instead of JSON Lines")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    source: Optional[TextIO] = None
    output: Optional[TextIO] = None
    close_source = close_output = False
    try:
        if args.input == "-":
            source = sys.stdin
        else:
            source = open(args.input, "r", encoding="utf-8")
            close_source = True
        value = load_json(source, args.input)

        if args.output == "-":
            output = sys.stdout
        else:
            output = open(args.output, "w", encoding="utf-8")
            close_output = True
        write_records(flatten(value), output, args.array)
    except (OSError, JSONFlattenError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if close_source and source is not None:
            source.close()
        if close_output and output is not None:
            output.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
