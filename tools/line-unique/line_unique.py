#!/usr/bin/env python3
"""Remove duplicate UTF-8 lines while retaining first-seen order."""

import argparse
import json
from pathlib import Path
import sys


def deduplicate(lines, ignore_case=False, strip=False, skip_blank=False):
    """Read binary LF/CRLF lines once; return first originals and counts."""
    entries = {}
    input_count = skipped = 0
    for raw in lines:
        input_count += 1
        text = raw.decode("utf-8")
        if text.endswith("\n"):
            text = text[:-1]
            if text.endswith("\r"):
                text = text[:-1]
        if skip_blank and not text.strip():
            skipped += 1
            continue
        key = text.strip() if strip else text
        if ignore_case:
            key = key.casefold()
        if key in entries:
            entries[key][1] += 1
        else:
            entries[key] = [text, 1]
    return list(entries.values()), {
        "input_lines": input_count,
        "unique_lines": len(entries),
        "duplicate_lines": input_count - skipped - len(entries),
        "skipped_blank_lines": skipped,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 text file, or '-' for stdin")
    parser.add_argument("--ignore-case", action="store_true",
                        help="compare with Unicode casefold")
    parser.add_argument("--strip", action="store_true",
                        help="ignore outer whitespace when comparing; preserve first original")
    parser.add_argument("--skip-blank", action="store_true",
                        help="skip whitespace-only lines")
    parser.add_argument("--counts", action="store_true",
                        help="prefix each retained line with count and a tab")
    parser.add_argument("--stats", action="store_true",
                        help="write JSON counts to stderr")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            entries, stats = deduplicate(sys.stdin.buffer, args.ignore_case,
                                         args.strip, args.skip_blank)
        else:
            with Path(args.input).open("rb") as handle:
                entries, stats = deduplicate(handle, args.ignore_case,
                                             args.strip, args.skip_blank)
    except (OSError, UnicodeError):
        print("error: input must be readable UTF-8 text", file=sys.stderr)
        return 2
    for original, count in entries:
        prefix = f"{count}\t" if args.counts else ""
        print(prefix + original)
    if args.stats:
        print(json.dumps(stats, separators=(",", ":")), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
