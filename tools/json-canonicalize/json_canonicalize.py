#!/usr/bin/env python3
"""Serialize JSON with recursively sorted object keys."""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple


class CanonicalizeError(ValueError):
    pass


def reject_constant(value: str) -> None:
    raise CanonicalizeError(f"non-standard number is not allowed: {value}")


def parse_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise CanonicalizeError(f"non-finite number is not allowed: {value}")
    return number


def unique_object(pairs: Iterable[Tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalizeError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def parse_json(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
            parse_float=parse_float,
        )
    except json.JSONDecodeError as exc:
        raise CanonicalizeError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def serialize(value: Any, indent: Optional[int], ascii_only: bool) -> str:
    separators = (",", ":") if indent is None else (",", ": ")
    return json.dumps(
        value,
        ensure_ascii=ascii_only,
        indent=indent,
        separators=separators,
        sort_keys=True,
        allow_nan=False,
    )


def read_text(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanonicalizeError(f"input is not valid UTF-8 at byte {exc.start}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sort JSON object keys recursively and write deterministic JSON text."
    )
    parser.add_argument("input", help="JSON file, or - for stdin")
    parser.add_argument("--indent", type=int, help="indentation width; default is compact")
    parser.add_argument("--ascii", action="store_true", help="escape non-ASCII characters")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.indent is not None and not 0 <= args.indent <= 16:
        parser.error("--indent must be between 0 and 16")

    try:
        value = parse_json(read_text(args.input))
        output = serialize(value, args.indent, args.ascii)
        sys.stdout.write(output + "\n")
    except (CanonicalizeError, OSError, UnicodeEncodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
