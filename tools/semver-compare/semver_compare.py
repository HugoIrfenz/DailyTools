#!/usr/bin/env python3
"""Compare two Semantic Version strings."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from functools import total_ordering
from typing import Optional


SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


class SemVerError(ValueError):
    """Raised for an invalid Semantic Version string."""


@total_ordering
@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...]
    build: tuple[str, ...]
    original: str

    @classmethod
    def parse(cls, value: str) -> "SemVer":
        match = SEMVER_RE.fullmatch(value)
        if match is None:
            raise SemVerError(f"invalid Semantic Version: {value!r}")
        pre = tuple(match.group(4).split(".")) if match.group(4) else ()
        build = tuple(match.group(5).split(".")) if match.group(5) else ()
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)), pre, build, value)

    def _core(self) -> tuple[int, int, int]:
        return self.major, self.minor, self.patch

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._core() == other._core() and self.prerelease == other.prerelease

    def __hash__(self) -> int:
        return hash((self._core(), self.prerelease))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        if self._core() != other._core():
            return self._core() < other._core()
        if not self.prerelease:
            return False
        if not other.prerelease:
            return True
        for left, right in zip(self.prerelease, other.prerelease):
            if left == right:
                continue
            left_numeric = left.isdigit()
            right_numeric = right.isdigit()
            if left_numeric and right_numeric:
                return int(left) < int(right)
            if left_numeric != right_numeric:
                return left_numeric
            return left < right
        return len(self.prerelease) < len(other.prerelease)


def compare(left: SemVer, right: SemVer) -> int:
    if left < right:
        return -1
    if left > right:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("--json", action="store_true", help="write structured JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        left = SemVer.parse(args.left)
        right = SemVer.parse(args.right)
    except SemVerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = compare(left, right)
    relation = {-1: "<", 0: "=", 1: ">"}[result]
    if args.json:
        json.dump(
            {"left": args.left, "right": args.right, "result": result, "relation": relation},
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        print(f"{args.left} {relation} {args.right}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
