#!/usr/bin/env python3
"""Summarize XML structure without printing element values."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Optional


DOCTYPE = re.compile(br"<!\s*DOCTYPE\b", re.IGNORECASE)


class XmlStatsError(ValueError):
    pass


def namespace_uri(name: str) -> Optional[str]:
    if name.startswith("{") and "}" in name:
        return name[1 : name.index("}")]
    return None


def summarize_xml(data: bytes) -> dict[str, Any]:
    if DOCTYPE.search(data):
        raise XmlStatsError("DOCTYPE declarations are not supported")

    elements = 0
    attributes = 0
    text_characters = 0
    depth = 0
    maximum_depth = 0
    root: Optional[str] = None
    tags: Counter[str] = Counter()
    namespaces: set[str] = set()

    for event, element in ET.iterparse(io.BytesIO(data), events=("start", "end")):
        if event == "start":
            depth += 1
            maximum_depth = max(maximum_depth, depth)
            elements += 1
            tags[element.tag] += 1
            if root is None:
                root = element.tag
            uri = namespace_uri(element.tag)
            if uri:
                namespaces.add(uri)
            attributes += len(element.attrib)
            for attribute_name in element.attrib:
                attribute_uri = namespace_uri(attribute_name)
                if attribute_uri:
                    namespaces.add(attribute_uri)
        else:
            text_characters += len(element.text or "") + len(element.tail or "")
            depth -= 1
            element.clear()

    if root is None:
        raise XmlStatsError("XML document has no root element")
    return {
        "root": root,
        "elements": elements,
        "attributes": attributes,
        "text_characters": text_characters,
        "max_depth": maximum_depth,
        "namespaces": sorted(namespaces),
        "tags": [
            {"name": name, "count": count} for name, count in sorted(tags.items())
        ],
    }


def read_input(path: str) -> bytes:
    return sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()


def render_text(summary: dict[str, Any]) -> str:
    lines = [
        f"root: {summary['root']}",
        f"elements: {summary['elements']}",
        f"attributes: {summary['attributes']}",
        f"text characters: {summary['text_characters']}",
        f"max depth: {summary['max_depth']}",
        f"namespaces: {len(summary['namespaces'])}",
        "tags:",
    ]
    lines.extend(f"  {item['count']}\t{item['name']}" for item in summary["tags"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize XML structure.")
    parser.add_argument("input", nargs="?", default="-", help="XML file or - for stdin")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = summarize_xml(read_input(args.input))
    except (OSError, ET.ParseError, XmlStatsError) as exc:
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
