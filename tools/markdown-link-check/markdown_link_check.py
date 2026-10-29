#!/usr/bin/env python3
"""Check local file targets referenced by common Markdown link forms."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import unquote, urlsplit


INLINE_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+[^)]*)?\)"
)
REFERENCE_DEFINITION = re.compile(
    r"^\s{0,3}\[[^\]]+\]:\s*(?:<([^>\n]+)>|(\S+))"
)
FENCE_START = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def strip_inline_code(line: str) -> str:
    result = list(line)
    index = 0
    while index < len(line):
        if line[index] != "`":
            index += 1
            continue
        end_ticks = index
        while end_ticks < len(line) and line[end_ticks] == "`":
            end_ticks += 1
        marker = line[index:end_ticks]
        closing = line.find(marker, end_ticks)
        if closing == -1:
            index = end_ticks
            continue
        for position in range(index, closing + len(marker)):
            result[position] = " "
        index = closing + len(marker)
    return "".join(result)


def extract_targets(text: str) -> list[tuple[int, str]]:
    targets: list[tuple[int, str]] = []
    fence: Optional[str] = None
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        fence_match = FENCE_START.match(raw_line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence is not None:
            continue
        line = strip_inline_code(raw_line)
        for match in INLINE_LINK.finditer(line):
            targets.append((line_number, match.group(1) or match.group(2)))
        reference = REFERENCE_DEFINITION.match(line)
        if reference:
            targets.append((line_number, reference.group(1) or reference.group(2)))
    return targets


def local_path(target: str) -> Optional[str]:
    if target.startswith("//"):
        return None
    try:
        parsed = urlsplit(target)
    except ValueError:
        return None
    if parsed.scheme or parsed.netloc:
        return None
    if not parsed.path or parsed.path.startswith("/"):
        return None
    return unquote(parsed.path)


def markdown_files(path: Path) -> Iterable[Path]:
    if path.is_dir():
        yield from sorted(item for item in path.rglob("*.md") if item.is_file())
    else:
        yield path


def check_file(path: Path, text: str) -> tuple[int, list[dict[str, Any]]]:
    checked = 0
    missing: list[dict[str, Any]] = []
    for line, target in extract_targets(text):
        relative = local_path(target)
        if relative is None:
            continue
        checked += 1
        resolved = path.parent.joinpath(relative).resolve(strict=False)
        if not resolved.exists():
            missing.append(
                {
                    "file": str(path),
                    "line": line,
                    "target": target,
                    "resolved": str(resolved),
                }
            )
    return checked, missing


def run_check(path: Path, stdin_text: Optional[str] = None, base: Optional[Path] = None) -> dict[str, Any]:
    checked = 0
    missing: list[dict[str, Any]] = []
    files = 0
    if stdin_text is not None:
        virtual_path = (base or Path.cwd()).resolve() / "stdin.md"
        count, errors = check_file(virtual_path, stdin_text)
        return {"files": 1, "local_links": count, "missing": errors}
    for file_path in markdown_files(path):
        text = file_path.read_text(encoding="utf-8")
        count, errors = check_file(file_path, text)
        files += 1
        checked += count
        missing.extend(errors)
    return {"files": files, "local_links": checked, "missing": missing}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check local targets in Markdown links.")
    parser.add_argument("path", help="Markdown file, directory, or - for stdin")
    parser.add_argument("--base", type=Path, help="base directory for stdin links")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.path == "-":
            summary = run_check(Path("-"), sys.stdin.read(), args.base)
        else:
            path = Path(args.path)
            if not path.exists():
                raise FileNotFoundError(path)
            summary = run_check(path)
    except (OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        for item in summary["missing"]:
            print(f"{item['file']}:{item['line']}: missing {item['target']}")
        print(
            f"checked {summary['local_links']} local links in {summary['files']} files; "
            f"missing {len(summary['missing'])}"
        )
    return 1 if summary["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
