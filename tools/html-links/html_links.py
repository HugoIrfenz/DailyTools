#!/usr/bin/env python3
"""Extract common link attributes from local HTML."""

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urljoin


LINK_ATTRIBUTES = {
    "a": "href",
    "area": "href",
    "audio": "src",
    "form": "action",
    "iframe": "src",
    "img": "src",
    "link": "href",
    "script": "src",
    "source": "src",
    "video": "src",
}


class LinksError(ValueError):
    pass


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: List[Tuple[str, str, str]] = []
        self.document_base: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        values = dict(attrs)
        if tag == "base" and self.document_base is None:
            value = values.get("href")
            if value:
                self.document_base = value.strip()
            return
        attribute = LINK_ATTRIBUTES.get(tag)
        if attribute:
            value = values.get(attribute)
            if value and value.strip():
                self.links.append((tag, attribute, value.strip()))

    def handle_startendtag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)


def extract(html: str, explicit_base: Optional[str], unique: bool) -> List[Dict[str, str]]:
    parser = LinkParser()
    try:
        parser.feed(html)
        parser.close()
    except (TypeError, ValueError) as exc:
        raise LinksError(f"could not parse HTML: {exc}") from exc
    base = explicit_base if explicit_base is not None else parser.document_base
    output = []
    seen = set()
    for tag, attribute, value in parser.links:
        resolved = urljoin(base, value) if base else value
        if unique and resolved in seen:
            continue
        seen.add(resolved)
        output.append({"tag": tag, "attribute": attribute, "value": value, "resolved": resolved})
    return output


def read_text(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LinksError(f"input is not valid UTF-8 at byte {exc.start}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract common href, src, and action links from HTML.")
    parser.add_argument("input", help="HTML file, or - for stdin")
    parser.add_argument("--base", help="base URL or path used to resolve relative links")
    parser.add_argument("--unique", action="store_true", help="retain only the first occurrence of each resolved link")
    parser.add_argument("--json", action="store_true", help="include tag, attribute, raw value, and resolved value")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        links = extract(read_text(args.input), args.base, args.unique)
        if args.json:
            sys.stdout.write(json.dumps(links, ensure_ascii=False, indent=2) + "\n")
        elif links:
            sys.stdout.write("\n".join(item["resolved"] for item in links) + "\n")
    except (LinksError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
