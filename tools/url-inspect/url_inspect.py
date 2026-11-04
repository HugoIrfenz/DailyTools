#!/usr/bin/env python3
"""Inspect URL structure without making network requests."""

import argparse
import ipaddress
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qsl, urlsplit


class UrlError(ValueError):
    pass


def inspect_url(value: str, line_number: int) -> Dict[str, object]:
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        raise UrlError(f"line {line_number}: URL contains whitespace or a control character")
    try:
        parsed = urlsplit(value)
        port = parsed.port
        host = parsed.hostname
    except ValueError as exc:
        raise UrlError(f"line {line_number}: invalid URL authority: {exc}") from exc
    ascii_host = None
    host_kind = None
    if host is not None:
        try:
            ipaddress.ip_address(host)
            host_kind = "ip"
            ascii_host = host
        except ValueError:
            host_kind = "name"
            try:
                ascii_host = host.encode("idna").decode("ascii")
            except UnicodeError as exc:
                raise UrlError(f"line {line_number}: host cannot be encoded as IDNA") from exc
    return {
        "line": line_number,
        "scheme": parsed.scheme or None,
        "has_authority": bool(parsed.netloc),
        "host": host,
        "ascii_host": ascii_host,
        "host_kind": host_kind,
        "port": port,
        "path": parsed.path,
        "path_segment_count": len([part for part in parsed.path.split("/") if part]),
        "query_parameter_count": len(parse_qsl(parsed.query, keep_blank_values=True)),
        "fragment_present": bool(parsed.fragment),
        "username_present": parsed.username is not None,
        "password_present": parsed.password is not None,
    }


def inspect_lines(text: str) -> List[Dict[str, object]]:
    results = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            results.append(inspect_url(line, line_number))
    return results


def read_text(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UrlError(f"input is not valid UTF-8 at byte {exc.start}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect one URL per line without network access.")
    parser.add_argument("input", help="text file containing URLs, or - for stdin")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = inspect_lines(read_text(args.input))
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    except (UrlError, OSError, UnicodeEncodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
