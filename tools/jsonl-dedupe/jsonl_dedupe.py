#!/usr/bin/env python3
"""Remove semantic duplicates from JSON Lines input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple


class JsonlDedupeError(ValueError):
    pass


def reject_constant(value: str) -> None:
    raise ValueError(f"non-standard number {value}")


def canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def pointer_tokens(pointer: str) -> List[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise JsonlDedupeError(f"invalid JSON Pointer {pointer!r}")
    tokens = []
    for token in pointer[1:].split("/"):
        index = 0
        while index < len(token):
            if token[index] == "~" and (index + 1 >= len(token) or token[index + 1] not in "01"):
                raise JsonlDedupeError(f"invalid JSON Pointer escape in {pointer!r}")
            index += 1
        tokens.append(token.replace("~1", "/").replace("~0", "~"))
    return tokens


def resolve_pointer(value: Any, pointer: str) -> Any:
    current = value
    for token in pointer_tokens(pointer):
        if isinstance(current, dict):
            if token not in current:
                raise JsonlDedupeError(f"pointer {pointer!r} does not exist")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit():
                raise JsonlDedupeError(f"pointer {pointer!r} does not select an array index")
            index = int(token)
            if index >= len(current):
                raise JsonlDedupeError(f"pointer {pointer!r} array index is out of range")
            current = current[index]
        else:
            raise JsonlDedupeError(f"pointer {pointer!r} traverses a scalar")
    return current


def parse_records(text: str) -> List[Tuple[int, Any]]:
    records = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line, parse_constant=reject_constant)
        except (json.JSONDecodeError, ValueError) as error:
            raise JsonlDedupeError(f"line {line_number}: invalid JSON: {error}") from error
        records.append((line_number, value))
    return records


def deduplicate(text: str, pointers: Sequence[str], keep: str = "first") -> Tuple[str, dict]:
    if keep not in {"first", "last"}:
        raise JsonlDedupeError("keep must be 'first' or 'last'")
    if len(pointers) != len(set(pointers)):
        raise JsonlDedupeError("key pointers must be unique")
    for pointer in pointers:
        pointer_tokens(pointer)

    records = parse_records(text)
    selected = {}
    keys = []
    for index, (line_number, value) in enumerate(records):
        try:
            if pointers:
                identity = tuple(canonical(resolve_pointer(value, pointer)) for pointer in pointers)
            else:
                identity = (canonical(value),)
        except JsonlDedupeError as error:
            raise JsonlDedupeError(f"line {line_number}: {error}") from error
        keys.append(identity)
        if identity not in selected or keep == "last":
            selected[identity] = index

    retained_indexes = sorted(selected.values())
    output = "\n".join(canonical(records[index][1]) for index in retained_indexes)
    if output:
        output += "\n"
    summary = {
        "records": len(records),
        "unique": len(retained_indexes),
        "duplicates": len(records) - len(retained_indexes),
        "keep": keep,
        "keys": list(pointers),
    }
    return output, summary


def read_source(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8-sig")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove semantic duplicates from JSON Lines.")
    parser.add_argument("path", nargs="?", default="-", help="JSONL file or - for stdin")
    parser.add_argument(
        "--key",
        action="append",
        default=[],
        help="JSON Pointer used as a key; repeat for a composite key",
    )
    parser.add_argument("--keep", choices=("first", "last"), default="first")
    parser.add_argument("--stats", action="store_true", help="write summary JSON to stderr")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit with status 1 when duplicates were found",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        output, summary = deduplicate(read_source(args.path), args.key, args.keep)
    except (OSError, UnicodeError, JsonlDedupeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    sys.stdout.write(output)
    if args.stats:
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")), file=sys.stderr)
    return 1 if args.check and summary["duplicates"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
