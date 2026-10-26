#!/usr/bin/env python3
"""Validate gzip data and summarize its decompressed bytes."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional


class GzipCheckError(ValueError):
    """Raised when gzip input is invalid or does not match expectations."""


def inspect_gzip(data: bytes) -> dict[str, object]:
    try:
        decompressed = gzip.decompress(data)
    except (gzip.BadGzipFile, EOFError, OSError) as exc:
        raise GzipCheckError(f"invalid gzip data: {exc}") from exc
    compressed_size = len(data)
    uncompressed_size = len(decompressed)
    return {
        "compressed_bytes": compressed_size,
        "uncompressed_bytes": uncompressed_size,
        "size_ratio": (uncompressed_size / compressed_size) if compressed_size else None,
        "sha256": hashlib.sha256(decompressed).hexdigest(),
    }


def format_text(stats: dict[str, object]) -> str:
    ratio = stats["size_ratio"]
    ratio_text = "n/a" if ratio is None else f"{ratio:.3f}"
    return "\n".join(
        [
            f"Compressed bytes: {stats['compressed_bytes']}",
            f"Uncompressed bytes: {stats['uncompressed_bytes']}",
            f"Uncompressed/compressed ratio: {ratio_text}",
            f"SHA-256 (uncompressed): {stats['sha256']}",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="gzip path, or - for stdin")
    parser.add_argument("--expect-sha256", metavar="HEX", help="require this uncompressed SHA-256")
    parser.add_argument("--json", action="store_true", help="write structured JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        stats = inspect_gzip(data)
        if args.expect_sha256 is not None:
            expected = args.expect_sha256.lower()
            if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
                raise GzipCheckError("expected SHA-256 must be exactly 64 hexadecimal characters")
            if stats["sha256"] != expected:
                raise GzipCheckError(f"SHA-256 mismatch: expected {expected}, got {stats['sha256']}")
    except (OSError, GzipCheckError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(stats, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(format_text(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
