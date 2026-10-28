#!/usr/bin/env python3
"""Summarize TAR archive metadata without extracting entries."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Optional


WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


def unsafe_path_reason(value: str) -> Optional[str]:
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or WINDOWS_ABSOLUTE.match(value):
        return "absolute path"
    if ".." in PurePosixPath(normalized).parts:
        return "parent traversal"
    return None


def suspicious_entry(member: tarfile.TarInfo) -> Optional[dict[str, str]]:
    reason = unsafe_path_reason(member.name)
    if reason:
        return {"name": member.name, "reason": reason}
    if member.issym() or member.islnk():
        link_reason = unsafe_path_reason(member.linkname)
        if link_reason:
            return {"name": member.name, "reason": f"link target: {link_reason}"}
    return None


def summarize(path: Path, top: int = 5) -> dict[str, Any]:
    with tarfile.open(path, mode="r:*") as archive:
        members = archive.getmembers()

    names = Counter(member.name for member in members)
    files = [member for member in members if member.isfile()]
    suspicious = [item for member in members if (item := suspicious_entry(member))]
    largest = sorted(files, key=lambda member: (-member.size, member.name))[:top]
    return {
        "archive": str(path),
        "members": len(members),
        "regular_files": len(files),
        "directories": sum(member.isdir() for member in members),
        "symlinks": sum(member.issym() for member in members),
        "hardlinks": sum(member.islnk() for member in members),
        "other_entries": sum(
            not (member.isfile() or member.isdir() or member.issym() or member.islnk())
            for member in members
        ),
        "logical_file_bytes": sum(member.size for member in files),
        "duplicate_names": [
            {"name": name, "count": count}
            for name, count in sorted(names.items())
            if count > 1
        ],
        "suspicious_entries": suspicious,
        "largest_files": [
            {"name": member.name, "size": member.size} for member in largest
        ],
    }


def render_text(summary: dict[str, Any]) -> str:
    lines = [
        f"archive: {summary['archive']}",
        f"members: {summary['members']}",
        f"regular files: {summary['regular_files']}",
        f"directories: {summary['directories']}",
        f"symlinks: {summary['symlinks']}",
        f"hardlinks: {summary['hardlinks']}",
        f"other entries: {summary['other_entries']}",
        f"logical file bytes: {summary['logical_file_bytes']}",
        f"duplicate names: {len(summary['duplicate_names'])}",
        f"suspicious entries: {len(summary['suspicious_entries'])}",
    ]
    if summary["largest_files"]:
        lines.append("largest files:")
        lines.extend(
            f"  {item['size']}\t{item['name']}" for item in summary["largest_files"]
        )
    return "\n".join(lines)


def non_negative_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value}") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize TAR archive metadata.")
    parser.add_argument("archive", type=Path, help="TAR archive path")
    parser.add_argument("--top", type=non_negative_int, default=5, help="largest files to list")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = summarize(args.archive, args.top)
    except (OSError, tarfile.TarError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
