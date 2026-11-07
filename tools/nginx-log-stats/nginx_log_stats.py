#!/usr/bin/env python3
"""Summarize Nginx/Apache Common or Combined access logs."""

from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple
from urllib.parse import urlsplit

LOG_LINE = re.compile(r'^\\S+\\s+\\S+\\s+\\S+\\s+\\[[^\\]]+\\]\\s+"((?:\\\\.|[^"\\\\])*)"\\s+(\\d{3}|-)\\s+(\\d+|-)(?:\\s+.*)?$')

class LogError(ValueError):
    pass

def parse_line(line: str) -> Optional[Tuple[str, str, str, int, bool]]:
    match = LOG_LINE.fullmatch(line)
    if not match:
        return None
    request = match.group(1).replace(r'\\"', '"').replace(r'\\\\', '\\\\')
    status = match.group(2)
    byte_text = match.group(3)
    if request == "-":
        method, path = "UNKNOWN", "UNKNOWN"
    else:
        parts = request.split()
        if len(parts) != 3:
            return None
        method, target, _protocol = parts
        try:
            parsed = urlsplit(target)
            path = target if method == "CONNECT" else (parsed.path or ("*" if target == "*" else "/"))
        except ValueError:
            return None
    return method, path, status, 0 if byte_text == "-" else int(byte_text), byte_text != "-"

def _top(counter: Counter, limit: int) -> list:
    return [{"value": value, "count": count} for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]

def summarize(source: str, top: int = 10, include_paths: bool = True) -> Dict[str, object]:
    if top < 1:
        raise LogError("top must be at least 1")
    methods: Counter = Counter()
    statuses: Counter = Counter()
    paths: Counter = Counter()
    parsed_count = 0
    malformed_count = 0
    total_bytes = 0
    known_byte_lines = 0
    for raw_line in source.splitlines():
        if not raw_line.strip():
            continue
        parsed = parse_line(raw_line)
        if parsed is None:
            malformed_count += 1
            continue
        method, path, status, byte_count, byte_known = parsed
        parsed_count += 1
        methods[method] += 1
        statuses[status] += 1
        if include_paths:
            paths[path] += 1
        total_bytes += byte_count
        if byte_known:
            known_byte_lines += 1
    return {
        "lines": parsed_count + malformed_count,
        "parsed": parsed_count,
        "malformed": malformed_count,
        "status_counts": dict(sorted(statuses.items())),
        "method_counts": dict(sorted(methods.items())),
        "client_errors": sum(count for status, count in statuses.items() if status.isdigit() and 400 <= int(status) < 500),
        "server_errors": sum(count for status, count in statuses.items() if status.isdigit() and 500 <= int(status) < 600),
        "bytes_known_lines": known_byte_lines,
        "total_bytes": total_bytes,
        "top_paths": _top(paths, top) if include_paths else [],
    }

def render_text(summary: Dict[str, object]) -> str:
    lines = [
        f"Lines: {summary['lines']} (parsed {summary['parsed']}, malformed {summary['malformed']})",
        f"Bytes: {summary['total_bytes']} across {summary['bytes_known_lines']} lines with a byte count",
        f"Client errors (4xx): {summary['client_errors']}",
        f"Server errors (5xx): {summary['server_errors']}",
        "Methods:",
    ]
    methods = summary["method_counts"]
    lines.extend(f"  {name}: {count}" for name, count in methods.items())
    lines.append("Statuses:")
    statuses = summary["status_counts"]
    lines.extend(f"  {name}: {count}" for name, count in statuses.items())
    if summary["top_paths"]:
        lines.append("Top paths:")
        lines.extend(f"  {item['value']}: {item['count']}" for item in summary["top_paths"])
    return "\\n".join(lines) + "\\n"

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Nginx/Apache Common or Combined access logs.")
    parser.add_argument("path", nargs="?", default="-", help="access log file or - for stdin")
    parser.add_argument("--top", type=int, default=10, help="number of paths to show (default: 10)")
    parser.add_argument("--no-paths", action="store_true", help="omit request paths from the report")
    parser.add_argument("--json", action="store_true", help="write the summary as JSON")
    return parser.parse_args(argv)

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        source = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8-sig")
        summary = summarize(source, args.top, not args.no_paths)
    except (OSError, UnicodeError, LogError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    else:
        sys.stdout.write(render_text(summary))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
