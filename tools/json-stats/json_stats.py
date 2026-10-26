#!/usr/bin/env python3
"""Summarize the structure and value types in a JSON document."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from typing import Any, Optional, TextIO


class JSONStatsError(ValueError):
    """Raised when JSON input is invalid or ambiguous."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JSONStatsError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise JSONStatsError(f"non-standard JSON number: {value}")


def load_json(stream: TextIO, source_name: str) -> Any:
    try:
        return json.load(stream, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except JSONStatsError:
        raise
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise JSONStatsError(f"invalid JSON in {source_name}: {exc}") from exc


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def collect_stats(root: Any) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    object_members = array_items = 0
    max_object_members = max_array_items = max_depth = 0
    stack: list[tuple[Any, int]] = [(root, 0)]

    while stack:
        value, depth = stack.pop()
        kind = type_name(value)
        counts[kind] += 1
        max_depth = max(max_depth, depth)
        if isinstance(value, dict):
            size = len(value)
            object_members += size
            max_object_members = max(max_object_members, size)
            for child in reversed(list(value.values())):
                stack.append((child, depth + 1))
        elif isinstance(value, list):
            size = len(value)
            array_items += size
            max_array_items = max(max_array_items, size)
            for child in reversed(value):
                stack.append((child, depth + 1))

    ordered_counts = {kind: counts[kind] for kind in ("object", "array", "string", "number", "boolean", "null")}
    return {
        "root_type": type_name(root),
        "nodes": sum(counts.values()),
        "max_depth": max_depth,
        "type_counts": ordered_counts,
        "object_members": object_members,
        "array_items": array_items,
        "max_object_members": max_object_members,
        "max_array_items": max_array_items,
    }


def format_text(stats: dict[str, Any]) -> str:
    types = ", ".join(f"{key}={value}" for key, value in stats["type_counts"].items())
    return "\n".join(
        [
            f"Root type: {stats['root_type']}",
            f"Nodes: {stats['nodes']}",
            f"Maximum depth: {stats['max_depth']}",
            f"Types: {types}",
            f"Object members: {stats['object_members']} (largest object: {stats['max_object_members']})",
            f"Array items: {stats['array_items']} (largest array: {stats['max_array_items']})",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 JSON path, or - for stdin")
    parser.add_argument("--json", action="store_true", help="write structured JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    source: Optional[TextIO] = None
    try:
        source = sys.stdin if args.input == "-" else open(args.input, "r", encoding="utf-8")
        stats = collect_stats(load_json(source, args.input))
    except (OSError, JSONStatsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if source is not None and source is not sys.stdin:
            source.close()

    if args.json:
        json.dump(stats, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(format_text(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
