#!/usr/bin/env python3
"""Generate a Markdown table of contents from ATX headings."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple


HEADING_RE = re.compile(r"^[ ]{0,3}(#{1,6})(?:[ \t]+|$)(.*)$")
FENCE_RE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$")
CLOSING_HASHES_RE = re.compile(r"[ \t]+#+[ \t]*$")


def slugify(text: str) -> str:
    """Create a deterministic, local anchor from heading text."""
    kept = []
    for char in text.casefold():
        category = unicodedata.category(char)
        if category[0] in {"L", "N"} or char in {"_", "-"} or char.isspace():
            kept.append(char)
    return re.sub(r"[\s-]+", "-", "".join(kept)).strip("-")


def escape_label(text: str) -> str:
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def iter_headings(lines: Iterable[str]) -> Iterable[Tuple[int, str]]:
    fence: Optional[Tuple[str, int]] = None

    for line in lines:
        line = line.rstrip("\r\n")
        if fence is not None:
            marker, minimum = fence
            closing = re.match(rf"^[ ]{{0,3}}{re.escape(marker)}{{{minimum},}}[ \t]*$", line)
            if closing:
                fence = None
            continue

        fence_match = FENCE_RE.match(line)
        if fence_match:
            run = fence_match.group(1)
            fence = (run[0], len(run))
            continue

        heading_match = HEADING_RE.match(line)
        if not heading_match:
            continue

        text = CLOSING_HASHES_RE.sub("", heading_match.group(2)).strip()
        if text:
            yield len(heading_match.group(1)), text


def build_toc(text: str, min_level: int = 2, max_level: int = 6) -> str:
    if not 1 <= min_level <= max_level <= 6:
        raise ValueError("heading levels must satisfy 1 <= min_level <= max_level <= 6")

    counts: dict[str, int] = {}
    entries = []
    for level, heading in iter_headings(text.splitlines()):
        if not min_level <= level <= max_level:
            continue
        base = slugify(heading)
        if not base:
            continue
        duplicate = counts.get(base, 0)
        counts[base] = duplicate + 1
        anchor = base if duplicate == 0 else f"{base}-{duplicate}"
        indent = "  " * (level - min_level)
        entries.append(f"{indent}- [{escape_label(heading)}](#{anchor})")
    return "\n".join(entries)


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8-sig")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown table of contents from ATX headings."
    )
    parser.add_argument("path", nargs="?", default="-", help="Markdown file or - for stdin")
    parser.add_argument("--min-level", type=int, default=2, choices=range(1, 7))
    parser.add_argument("--max-level", type=int, default=6, choices=range(1, 7))
    args = parser.parse_args(argv)
    if args.min_level > args.max_level:
        parser.error("--min-level cannot be greater than --max-level")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        source = read_input(args.path)
        toc = build_toc(source, args.min_level, args.max_level)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if toc:
        print(toc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
