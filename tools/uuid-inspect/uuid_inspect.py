#!/usr/bin/env python3
"""Normalize UUIDs and display their encoded metadata."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from typing import Iterable, Optional


class UUIDInspectError(ValueError):
    """Raised when UUID input is missing or invalid."""


VARIANT_NAMES = {
    uuid.RESERVED_NCS: "ncs",
    uuid.RFC_4122: "rfc4122",
    uuid.RESERVED_MICROSOFT: "microsoft",
    uuid.RESERVED_FUTURE: "future",
}


def inspect_uuid(value: str) -> dict[str, object]:
    text = value.strip()
    if not text:
        raise UUIDInspectError("UUID value is empty")
    try:
        parsed = uuid.UUID(text)
    except (ValueError, AttributeError) as exc:
        raise UUIDInspectError(f"invalid UUID: {value!r}") from exc

    return {
        "input": value,
        "canonical": str(parsed),
        "hex": parsed.hex,
        "urn": parsed.urn,
        "integer": parsed.int,
        "variant": VARIANT_NAMES.get(parsed.variant, str(parsed.variant)),
        "version": parsed.version,
        "is_nil": parsed.int == 0,
        "is_max": parsed.int == (1 << 128) - 1,
    }


def parse_values(arguments: Iterable[str], stdin_text: Optional[str] = None) -> list[str]:
    values = list(arguments)
    if values:
        return values
    text = sys.stdin.read() if stdin_text is None else stdin_text
    values = [line.strip() for line in text.splitlines() if line.strip()]
    if not values:
        raise UUIDInspectError("provide a UUID argument or non-empty stdin")
    return values


def format_text(item: dict[str, object]) -> str:
    fields = [
        f"UUID: {item['canonical']}",
        f"Version: {item['version'] if item['version'] is not None else 'none'}",
        f"Variant: {item['variant']}",
        f"Hex: {item['hex']}",
        f"URN: {item['urn']}",
        f"Integer: {item['integer']}",
        f"Nil: {'yes' if item['is_nil'] else 'no'}",
        f"Max: {'yes' if item['is_max'] else 'no'}",
    ]
    return "\n".join(fields)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("values", nargs="*", help="UUID values; reads non-empty stdin lines when omitted")
    parser.add_argument("--json", action="store_true", help="write a JSON array")
    parser.add_argument(
        "--require-version",
        type=int,
        choices=range(1, 16),
        metavar="N",
        help="exit 1 unless every UUID has version N",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        items = [inspect_uuid(value) for value in parse_values(args.values)]
        if args.require_version is not None:
            mismatches = [item["canonical"] for item in items if item["version"] != args.require_version]
            if mismatches:
                raise UUIDInspectError(
                    f"{len(mismatches)} UUID(s) do not have version {args.require_version}: "
                    + ", ".join(str(value) for value in mismatches)
                )
    except UUIDInspectError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write("\n\n".join(format_text(item) for item in items) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
