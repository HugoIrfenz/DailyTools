#!/usr/bin/env python3
"""Convert Unix permission bits between octal and symbolic forms."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Optional


OCTAL_RE = re.compile(r"^(?:0)?([0-7]{3,4})$")
SYMBOLIC_RE = re.compile(r"^[r-][w-][xSs-][r-][w-][xSs-][r-][w-][xTt-]$")


class UnixModeError(ValueError):
    """Raised when a permission mode is not recognized."""


def parse_symbolic(value: str) -> int:
    if SYMBOLIC_RE.fullmatch(value) is None:
        raise UnixModeError(f"invalid symbolic mode: {value!r}")

    mode = 0
    triples = ((0, 0o400, 0o200, 0o100, 0o4000), (3, 0o040, 0o020, 0o010, 0o2000), (6, 0o004, 0o002, 0o001, 0o1000))
    for offset, read_bit, write_bit, execute_bit, special_bit in triples:
        if value[offset] == "r":
            mode |= read_bit
        if value[offset + 1] == "w":
            mode |= write_bit
        execute = value[offset + 2]
        if execute in "xst":
            mode |= execute_bit
        if execute in "sStT":
            mode |= special_bit
    return mode


def parse_mode(value: str) -> int:
    octal = OCTAL_RE.fullmatch(value)
    if octal is not None:
        mode = int(octal.group(1), 8)
        if mode > 0o7777:
            raise UnixModeError(f"octal mode is out of range: {value!r}")
        return mode
    if value.isdigit():
        raise UnixModeError(f"invalid octal mode: {value!r}")
    return parse_symbolic(value)


def execute_character(mode: int, execute_bit: int, special_bit: int, lower: str, upper: str) -> str:
    executable = bool(mode & execute_bit)
    special = bool(mode & special_bit)
    if special:
        return lower if executable else upper
    return "x" if executable else "-"


def format_symbolic(mode: int) -> str:
    return "".join(
        [
            "r" if mode & 0o400 else "-",
            "w" if mode & 0o200 else "-",
            execute_character(mode, 0o100, 0o4000, "s", "S"),
            "r" if mode & 0o040 else "-",
            "w" if mode & 0o020 else "-",
            execute_character(mode, 0o010, 0o2000, "s", "S"),
            "r" if mode & 0o004 else "-",
            "w" if mode & 0o002 else "-",
            execute_character(mode, 0o001, 0o1000, "t", "T"),
        ]
    )


def describe(value: str) -> dict[str, object]:
    mode = parse_mode(value)
    return {
        "input": value,
        "octal": f"{mode:04o}",
        "symbolic": format_symbolic(mode),
        "special": {
            "setuid": bool(mode & 0o4000),
            "setgid": bool(mode & 0o2000),
            "sticky": bool(mode & 0o1000),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modes", nargs="+", help="octal or nine-character symbolic modes")
    parser.add_argument("--json", action="store_true", help="write a JSON array")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        items = [describe(value) for value in args.modes]
    except UnixModeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(items, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for item in items:
            print(f"{item['input']}: {item['octal']} {item['symbolic']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
