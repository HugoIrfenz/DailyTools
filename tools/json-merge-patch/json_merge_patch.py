#!/usr/bin/env python3
"""Apply a JSON Merge Patch document to a JSON value."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Optional, TextIO


class MergePatchError(ValueError):
    """Raised for ambiguous or invalid JSON input."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MergePatchError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise MergePatchError(f"non-standard JSON number: {value}")


def load_json(stream: TextIO, source_name: str) -> Any:
    try:
        return json.load(
            stream,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except MergePatchError:
        raise
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise MergePatchError(f"invalid JSON in {source_name}: {exc}") from exc


def merge_patch(target: Any, patch: Any) -> Any:
    """Return the result of applying JSON Merge Patch semantics."""
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)

    result = copy.deepcopy(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = merge_patch(result.get(key), value)
    return result


def open_input(path: str) -> tuple[TextIO, bool]:
    if path == "-":
        return sys.stdin, False
    return open(path, "r", encoding="utf-8"), True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="target JSON path, or - for stdin")
    parser.add_argument("patch", help="merge-patch JSON path")
    parser.add_argument("-o", "--output", default="-", help="output path (default: stdout)")
    parser.add_argument("--compact", action="store_true", help="write JSON on one line")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.patch == "-":
        print("error: patch must be a file path; stdin is reserved for target", file=sys.stderr)
        return 1

    target_stream: Optional[TextIO] = None
    patch_stream: Optional[TextIO] = None
    output_stream: Optional[TextIO] = None
    close_target = close_patch = close_output = False
    try:
        target_stream, close_target = open_input(args.target)
        patch_stream = open(args.patch, "r", encoding="utf-8")
        close_patch = True
        target = load_json(target_stream, args.target)
        patch = load_json(patch_stream, args.patch)
        result = merge_patch(target, patch)

        if args.output == "-":
            output_stream = sys.stdout
        else:
            output_stream = open(args.output, "w", encoding="utf-8")
            close_output = True
        if args.compact:
            json.dump(result, output_stream, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        else:
            json.dump(result, output_stream, ensure_ascii=False, indent=2, allow_nan=False)
        output_stream.write("\n")
    except (OSError, MergePatchError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if close_target and target_stream is not None:
            target_stream.close()
        if close_patch and patch_stream is not None:
            patch_stream.close()
        if close_output and output_stream is not None:
            output_stream.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
