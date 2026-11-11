#!/usr/bin/env python3
"""Inspect the structure of a raw HTTP header block without printing values."""
import argparse
import json
import re
import sys
from pathlib import Path

TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
MAX_BYTES = 1024 * 1024


def inspect_headers(data):
    if len(data) > MAX_BYTES:
        raise ValueError("input exceeds 1 MiB")
    if b"\x00" in data:
        raise ValueError("NUL bytes are not supported")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("input must be UTF-8") from exc
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        raise ValueError("bare CR line endings are not supported")
    lines = text.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return {"has_start_line": False, "field_count": 0, "unique_name_count": 0,
                "duplicate_names": [], "total_value_characters": 0, "headers": []}
    if "" in lines:
        raise ValueError("content after the header terminator is not supported")

    has_start = ":" not in lines[0]
    header_lines = lines[1:] if has_start else lines
    if has_start and (not lines[0].strip() or any(ord(c) < 32 or ord(c) == 127 for c in lines[0])):
        raise ValueError("invalid start line")

    ordered = []
    records = {}
    total_values = 0
    for number, line in enumerate(header_lines, 2 if has_start else 1):
        if line.startswith((" ", "\t")):
            raise ValueError("obsolete folded header at line " + str(number))
        if ":" not in line:
            raise ValueError("missing colon at line " + str(number))
        raw_name, raw_value = line.split(":", 1)
        if not TOKEN.fullmatch(raw_name):
            raise ValueError("invalid header name at line " + str(number))
        if any((ord(c) < 32 and c != "\t") or ord(c) == 127 for c in raw_value):
            raise ValueError("invalid control character at line " + str(number))
        name = raw_name.lower()
        value_length = len(raw_value.strip(" \t"))
        total_values += value_length
        if name not in records:
            ordered.append(name)
            records[name] = {"name": name, "count": 0, "value_characters": 0}
        records[name]["count"] += 1
        records[name]["value_characters"] += value_length

    headers = [records[name] for name in ordered]
    return {"has_start_line": has_start, "field_count": len(header_lines),
            "unique_name_count": len(headers),
            "duplicate_names": [item["name"] for item in headers if item["count"] > 1],
            "total_value_characters": total_values, "headers": headers}


def format_text(result):
    rows = ["start_line\t" + ("yes" if result["has_start_line"] else "no"),
            "fields\t" + str(result["field_count"]),
            "unique_names\t" + str(result["unique_name_count"]),
            "value_characters\t" + str(result["total_value_characters"]),
            "name\tcount\tvalue_characters"]
    rows.extend(f'{item["name"]}\t{item["count"]}\t{item["value_characters"]}'
                for item in result["headers"])
    return "\n".join(rows) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="raw header file, or - for stdin")
    parser.add_argument("--text", action="store_true", help="emit tab-separated text instead of JSON")
    args = parser.parse_args(argv)
    try:
        data = sys.stdin.buffer.read(MAX_BYTES + 1) if args.input == "-" else Path(args.input).read_bytes()
        result = inspect_headers(data)
        output = format_text(result) if args.text else json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        sys.stdout.write(output)
    except BrokenPipeError:
        return 0
    except (OSError, ValueError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
