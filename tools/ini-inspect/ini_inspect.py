#!/usr/bin/env python3
"""Inventory INI sections and keys without printing values."""

import argparse
import configparser
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


class InspectError(ValueError):
    pass


def describe_parse_error(exc: configparser.Error) -> str:
    if isinstance(exc, configparser.DuplicateSectionError):
        return f"duplicate section {exc.section!r} at line {exc.lineno}"
    if isinstance(exc, configparser.DuplicateOptionError):
        return (
            f"duplicate option {exc.option!r} in section {exc.section!r} "
            f"at line {exc.lineno}"
        )
    if isinstance(exc, configparser.MissingSectionHeaderError):
        return f"missing section header at line {exc.lineno}"
    if isinstance(exc, configparser.ParsingError):
        lines = sorted({line for line, _ in exc.errors})
        suffix = ", ".join(str(line) for line in lines)
        return f"invalid INI syntax at line(s): {suffix}"
    return f"invalid INI: {type(exc).__name__}"


def inspect_ini(text: str) -> Dict[str, object]:
    parser = configparser.ConfigParser(
        interpolation=None,
        strict=True,
        allow_no_value=True,
        empty_lines_in_values=True,
    )
    parser.optionxform = str
    try:
        parser.read_string(text, source="<input>")
    except configparser.Error as exc:
        raise InspectError(describe_parse_error(exc)) from exc
    except AttributeError as exc:
        # Python 3.9-3.12 can raise AttributeError when an indented
        # continuation follows an option declared without a value.
        raise InspectError(
            "invalid INI syntax: continuation after an option without a value"
        ) from exc

    default_keys = list(parser.defaults())
    sections = []
    for name in parser.sections():
        keys = list(parser._sections[name])
        sections.append({"name": name, "key_count": len(keys), "keys": keys})
    return {
        "section_count": len(sections),
        "key_count": len(default_keys) + sum(section["key_count"] for section in sections),
        "default_keys": default_keys,
        "sections": sections,
    }


def render_text(result: Dict[str, object]) -> str:
    lines = [
        f"Sections: {result['section_count']}",
        f"Keys: {result['key_count']}",
        f"[DEFAULT] ({len(result['default_keys'])})",
    ]
    lines.extend(f"  {key}" for key in result["default_keys"])
    for section in result["sections"]:
        lines.append(f"[{section['name']}] ({section['key_count']})")
        lines.extend(f"  {key}" for key in section["keys"])
    return "\n".join(lines)


def read_text(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InspectError(f"input is not valid UTF-8 at byte {exc.start}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List INI sections and key names without printing values."
    )
    parser.add_argument("input", help="INI file, or - for stdin")
    parser.add_argument("--text", action="store_true", help="write a plain-text report instead of JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = inspect_ini(read_text(args.input))
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
