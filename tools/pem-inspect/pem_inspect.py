#!/usr/bin/env python3
"""Inventory strict base64-only PEM blocks without parsing their payloads."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Optional


BOUNDARY_RE = re.compile(rb"^-----(BEGIN|END) ([!-~]+)-----$")
BASE64_RE = re.compile(rb"^[A-Za-z0-9+/]*={0,2}$")


class PEMInspectError(ValueError):
    """Raised when PEM armor is malformed or ambiguous."""


def inspect_pem(data: bytes) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    label: Optional[str] = None
    payload: list[bytes] = []
    begin_line = 0

    for line_number, raw_line in enumerate(data.splitlines(), start=1):
        line = raw_line.strip()
        boundary = BOUNDARY_RE.fullmatch(line)
        if label is None:
            if not line:
                continue
            if boundary is None or boundary.group(1) != b"BEGIN":
                raise PEMInspectError(f"unexpected content on line {line_number}")
            label = boundary.group(2).decode("ascii")
            payload = []
            begin_line = line_number
            continue

        if boundary is not None:
            kind = boundary.group(1)
            boundary_label = boundary.group(2).decode("ascii")
            if kind == b"BEGIN":
                raise PEMInspectError(f"nested BEGIN on line {line_number}")
            if boundary_label != label:
                raise PEMInspectError(
                    f"END label {boundary_label!r} does not match {label!r} on line {line_number}"
                )
            if not payload:
                raise PEMInspectError(f"empty PEM block beginning on line {begin_line}")
            encoded = b"".join(payload)
            try:
                decoded = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise PEMInspectError(f"invalid base64 in block beginning on line {begin_line}") from exc
            blocks.append(
                {
                    "index": len(blocks) + 1,
                    "label": label,
                    "bytes": len(decoded),
                    "sha256": hashlib.sha256(decoded).hexdigest(),
                    "begin_line": begin_line,
                    "end_line": line_number,
                }
            )
            label = None
            payload = []
            continue

        if not line or BASE64_RE.fullmatch(line) is None:
            raise PEMInspectError(f"invalid base64 line {line_number}")
        payload.append(line)

    if label is not None:
        raise PEMInspectError(f"unterminated {label!r} block beginning on line {begin_line}")
    if not blocks:
        raise PEMInspectError("no PEM blocks found")

    counts = Counter(str(block["sha256"]) for block in blocks)
    for block in blocks:
        block["duplicate_payload"] = counts[str(block["sha256"])] > 1
    return blocks


def format_text(blocks: list[dict[str, object]]) -> str:
    lines = []
    for block in blocks:
        duplicate = " duplicate" if block["duplicate_payload"] else ""
        lines.append(
            f"{block['index']}: {block['label']} — {block['bytes']} bytes — "
            f"sha256:{block['sha256']}{duplicate}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="PEM path, or - for stdin")
    parser.add_argument("--json", action="store_true", help="write structured JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        blocks = inspect_pem(data)
    except (OSError, PEMInspectError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(blocks, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(format_text(blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
