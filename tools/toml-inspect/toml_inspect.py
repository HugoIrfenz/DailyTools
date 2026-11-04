#!/usr/bin/env python3
"""Inventory TOML keys and value types without printing values."""

import argparse
import datetime
import json
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional


class InspectError(ValueError):
    pass


def type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, datetime.datetime):
        return "datetime"
    if isinstance(value, datetime.date):
        return "date"
    if isinstance(value, datetime.time):
        return "time"
    if isinstance(value, list):
        if not value:
            return "array<empty>"
        if all(isinstance(item, dict) for item in value):
            return "array<table>"
        kinds = sorted({type_name(item) for item in value})
        return "array<" + "|".join(kinds) + ">"
    if isinstance(value, dict):
        return "table"
    return type(value).__name__


def inspect_toml(text: str) -> Dict[str, object]:
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise InspectError(f"invalid TOML: {exc}") from exc

    tables: List[Dict[str, object]] = []

    def walk(table: Dict[str, Any], path: List[str]) -> None:
        keys = []
        children = []
        for name, value in table.items():
            if isinstance(value, dict):
                children.append((value, path + [name]))
                continue
            entry: Dict[str, object] = {"name": name, "type": type_name(value)}
            if isinstance(value, list):
                entry["length"] = len(value)
            keys.append(entry)
            if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                for index, item in enumerate(value):
                    children.append((item, path + [name, str(index)]))
        tables.append({"path": path, "key_count": len(keys), "keys": keys})
        for child, child_path in children:
            walk(child, child_path)

    walk(document, [])
    return {
        "table_count": len(tables),
        "value_key_count": sum(table["key_count"] for table in tables),
        "tables": tables,
    }


def render_text(result: Dict[str, object]) -> str:
    lines = [f"Tables: {result['table_count']}", f"Value keys: {result['value_key_count']}"]
    for table in result["tables"]:
        name = ".".join(table["path"]) if table["path"] else "<root>"
        lines.append(f"[{name}] ({table['key_count']})")
        for key in table["keys"]:
            suffix = f", length={key['length']}" if "length" in key else ""
            lines.append(f"  {key['name']}: {key['type']}{suffix}")
    return "\n".join(lines)


def read_text(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InspectError(f"input is not valid UTF-8 at byte {exc.start}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List TOML table paths, key names, and value types without printing values.")
    parser.add_argument("input", help="TOML file, or - for stdin")
    parser.add_argument("--text", action="store_true", help="write plain text instead of JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = inspect_toml(read_text(args.input))
        output = render_text(result) if args.text else json.dumps(result, ensure_ascii=False, indent=2)
        sys.stdout.write(output + "\n")
    except (InspectError, OSError, UnicodeEncodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
