#!/usr/bin/env python3
"""Replace selected JSON values addressed by JSON Pointer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional


class RedactError(ValueError):
    pass


class PathNotFound(RedactError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RedactError(f"duplicate object key: {key}")
        result[key] = value
    return result


def decode_token(token: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(token):
        if token[index] != "~":
            result.append(token[index])
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in "01":
            raise RedactError("invalid JSON Pointer escape")
        result.append("~" if token[index + 1] == "0" else "/")
        index += 2
    return "".join(result)


def pointer_tokens(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise RedactError("JSON Pointer must be empty or start with /")
    return [decode_token(token) for token in pointer[1:].split("/")]


def array_index(token: str, length: int) -> int:
    if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
        raise RedactError(f"invalid array index: {token}")
    index = int(token)
    if index >= length:
        raise PathNotFound(f"array index out of range: {token}")
    return index


def replace_pointer(document: Any, pointer: str, replacement: str) -> Any:
    tokens = pointer_tokens(pointer)
    if not tokens:
        return replacement
    current = document
    for token in tokens[:-1]:
        if isinstance(current, dict):
            if token not in current:
                raise PathNotFound(f"path not found: {pointer}")
            current = current[token]
        elif isinstance(current, list):
            current = current[array_index(token, len(current))]
        else:
            raise PathNotFound(f"path not found: {pointer}")
    final = tokens[-1]
    if isinstance(current, dict):
        if final not in current:
            raise PathNotFound(f"path not found: {pointer}")
        current[final] = replacement
    elif isinstance(current, list):
        current[array_index(final, len(current))] = replacement
    else:
        raise PathNotFound(f"path not found: {pointer}")
    return document


def redact(document: Any, pointers: list[str], replacement: str, ignore_missing: bool) -> Any:
    for pointer in pointers:
        try:
            document = replace_pointer(document, pointer, replacement)
        except PathNotFound:
            if not ignore_missing:
                raise
    return document


def read_json(path: str) -> Any:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replace JSON values selected by JSON Pointer.")
    parser.add_argument("input", nargs="?", default="-", help="JSON file or - for stdin")
    parser.add_argument("--path", action="append", required=True, dest="paths", help="JSON Pointer to redact; repeatable")
    parser.add_argument("--replacement", default="[REDACTED]", help="replacement string")
    parser.add_argument("--ignore-missing", action="store_true", help="skip paths that cannot be resolved")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = read_json(args.input)
        document = redact(document, args.paths, args.replacement, args.ignore_missing)
    except (OSError, UnicodeError, json.JSONDecodeError, RedactError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.compact:
        json.dump(document, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    else:
        json.dump(document, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
