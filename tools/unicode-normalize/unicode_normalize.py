#!/usr/bin/env python3
"""Normalize UTF-8 text with a selected Unicode normalization form."""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path


FORMS = ("NFC", "NFD", "NFKC", "NFKD")


def decode_utf8(data: bytes) -> str:
    return data.decode("utf-8")


def normalize_text(text: str, form: str = "NFC") -> str:
    if form not in FORMS:
        raise ValueError(f"unsupported normalization form: {form}")
    return unicodedata.normalize(form, text)


def read_input(path: str) -> bytes:
    if path == "-":
        return sys.stdin.buffer.read()
    return Path(path).read_bytes()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize UTF-8 text as NFC, NFD, NFKC, or NFKD."
    )
    parser.add_argument("input", nargs="?", default="-", help="UTF-8 file or - for stdin")
    parser.add_argument(
        "--form",
        choices=FORMS,
        default="NFC",
        help="normalization form (default: NFC)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="write no text; exit 1 when normalization would change the input",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text = decode_utf8(read_input(args.input))
    except (OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.check:
        if unicodedata.is_normalized(args.form, text):
            print(f"normalized ({args.form})", file=sys.stderr)
            return 0
        print(f"normalization required ({args.form})", file=sys.stderr)
        return 1

    normalized = normalize_text(text, args.form)
    try:
        sys.stdout.buffer.write(normalized.encode("utf-8"))
    except (BrokenPipeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
