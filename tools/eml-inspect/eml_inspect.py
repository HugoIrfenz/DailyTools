#!/usr/bin/env python3
"""Inventory RFC email headers and MIME parts without printing bodies."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from email import policy
from email.message import Message
from email.parser import BytesParser
from pathlib import Path
from typing import Dict, List, Optional


def payload_bytes(part: Message) -> bytes:
    decoded = part.get_payload(decode=True)
    if decoded is not None:
        return decoded
    payload = part.get_payload()
    if isinstance(payload, str):
        return payload.encode("utf-8", errors="surrogateescape")
    return b""


def inspect_message(data: bytes) -> Dict[str, object]:
    message = BytesParser(policy=policy.default).parsebytes(data)

    header_order: List[str] = []
    header_counts: Dict[str, int] = {}
    display_names: Dict[str, str] = {}
    for name, _ in message.raw_items():
        key = name.lower()
        if key not in header_counts:
            header_order.append(key)
            display_names[key] = name
            header_counts[key] = 0
        header_counts[key] += 1
    headers = [
        {"name": display_names[key], "count": header_counts[key]}
        for key in header_order
    ]

    parts = []
    attachment_count = 0
    defects: Counter[str] = Counter()
    for part in message.walk():
        defects.update(type(defect).__name__ for defect in part.defects)
        if part.is_multipart():
            continue
        payload = payload_bytes(part)
        disposition = part.get_content_disposition()
        filename = part.get_filename()
        if disposition == "attachment" or filename is not None:
            attachment_count += 1
        parts.append(
            {
                "index": len(parts) + 1,
                "content_type": part.get_content_type(),
                "disposition": disposition,
                "filename": filename,
                "decoded_size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "defects": [type(defect).__name__ for defect in part.defects],
            }
        )

    return {
        "header_count": sum(header_counts.values()),
        "unique_header_count": len(headers),
        "headers": headers,
        "multipart": message.is_multipart(),
        "leaf_part_count": len(parts),
        "attachment_count": attachment_count,
        "defects": [
            {"name": name, "count": count}
            for name, count in sorted(defects.items())
        ],
        "parts": parts,
    }


def render_text(result: Dict[str, object]) -> str:
    lines = [
        f"Headers: {result['header_count']} ({result['unique_header_count']} unique)",
        f"Multipart: {'yes' if result['multipart'] else 'no'}",
        f"Leaf parts: {result['leaf_part_count']}",
        f"Attachments: {result['attachment_count']}",
        "Header names:",
    ]
    lines.extend(f"  {item['name']} ({item['count']})" for item in result["headers"])
    lines.append("Parts:")
    for part in result["parts"]:
        suffix = f", filename={part['filename']!r}" if part["filename"] is not None else ""
        lines.append(
            f"  {part['index']}: {part['content_type']}, {part['decoded_size']} bytes, "
            f"sha256={part['sha256']}{suffix}"
        )
    if result["defects"]:
        lines.append("Defects:")
        lines.extend(f"  {item['name']} ({item['count']})" for item in result["defects"])
    return "\n".join(lines)


def read_bytes(path: str) -> bytes:
    return sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory email headers and MIME payload metadata without printing bodies."
    )
    parser.add_argument("input", help="EML file, or - for stdin")
    parser.add_argument("--text", action="store_true", help="write a plain-text report instead of JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = inspect_message(read_bytes(args.input))
        output = render_text(result) if args.text else json.dumps(result, ensure_ascii=False, indent=2)
        sys.stdout.write(output + "\n")
    except (OSError, UnicodeEncodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
