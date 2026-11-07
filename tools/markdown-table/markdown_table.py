#!/usr/bin/env python3
"""Align GitHub-flavored Markdown pipe tables."""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence

class TableError(ValueError):
    pass

SEPARATOR = re.compile(r"^:?-{3,}:?$")

def split_row(line: str) -> List[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        backslashes = 0
        index = len(text) - 2
        while index >= 0 and text[index] == "\\":
            backslashes += 1
            index -= 1
        if backslashes % 2 == 0:
            text = text[:-1]
    cells: List[str] = []
    current: List[str] = []
    code_ticks = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            current.append(char)
            current.append(text[index + 1])
            index += 2
            continue
        if char == "`":
            end = index + 1
            while end < len(text) and text[end] == "`":
                end += 1
            run = end - index
            if code_ticks == 0:
                code_ticks = run
            elif code_ticks == run:
                code_ticks = 0
            current.extend(text[index:end])
            index = end
            continue
        if char == "|" and code_ticks == 0:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells

def is_separator(cells: Sequence[str]) -> bool:
    return len(cells) >= 2 and all(SEPARATOR.fullmatch(cell) for cell in cells)

def _alignment(separator: str) -> str:
    left = separator.startswith(":")
    right = separator.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left"
    return "default"

def _format_row(cells: Sequence[str], widths: Sequence[int], alignments: Sequence[str]) -> str:
    rendered = []
    for cell, width, alignment in zip(cells, widths, alignments):
        if alignment == "right":
            rendered.append(cell.rjust(width))
        elif alignment == "center":
            rendered.append(cell.center(width))
        else:
            rendered.append(cell.ljust(width))
    return "| " + " | ".join(rendered) + " |"

def _format_separator(widths: Sequence[int], alignments: Sequence[str]) -> str:
    cells = []
    for width, alignment in zip(widths, alignments):
        left = ":" if alignment in {"center", "left"} else ""
        right = ":" if alignment in {"center", "right"} else ""
        dashes = "-" * max(3, width - len(left) - len(right))
        cells.append(left + dashes + right)
    return "| " + " | ".join(cells) + " |"

def format_markdown(source: str) -> str:
    lines = source.splitlines()
    output: List[str] = []
    index = 0
    while index < len(lines):
        if index + 1 < len(lines):
            header = split_row(lines[index])
            separator = split_row(lines[index + 1])
            if len(header) >= 2 and len(header) == len(separator) and is_separator(separator):
                table_rows = [header]
                row_index = index + 2
                while row_index < len(lines):
                    candidate = split_row(lines[row_index])
                    if len(candidate) < 2:
                        break
                    if len(candidate) != len(header):
                        raise TableError(f"line {row_index + 1}: expected {len(header)} columns, found {len(candidate)}")
                    table_rows.append(candidate)
                    row_index += 1
                widths = [max(len(row[column]) for row in table_rows) for column in range(len(header))]
                alignments = [_alignment(cell) for cell in separator]
                output.append(_format_row(header, widths, alignments))
                output.append(_format_separator(widths, alignments))
                output.extend(_format_row(row, widths, alignments) for row in table_rows[1:])
                index = row_index
                continue
        output.append(lines[index])
        index += 1
    rendered = "\n".join(output)
    if source.endswith(("\n", "\r")):
        rendered += "\n"
    return rendered

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Align GitHub-flavored Markdown pipe tables.")
    parser.add_argument("path", nargs="?", default="-", help="Markdown file or - for stdin")
    return parser.parse_args(argv)

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        source = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8-sig")
        sys.stdout.write(format_markdown(source))
    except (OSError, UnicodeError, TableError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
