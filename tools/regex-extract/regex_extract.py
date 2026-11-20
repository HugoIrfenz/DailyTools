"""Extract regular expression matches as JSON Lines from UTF-8 text."""
import argparse
import json
import re
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern", help="Python regular expression")
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--ignore-case", action="store_true")
    args = parser.parse_args()
    try:
        pattern = re.compile(args.pattern, re.IGNORECASE if args.ignore_case else 0)
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        text = data.decode("utf-8-sig")
        for match in pattern.finditer(text):
            print(json.dumps({
                "start": match.start(),
                "end": match.end(),
                "match": match.group(),
                "groups": match.groups(),
                "named_groups": match.groupdict(),
            }, ensure_ascii=True))
    except (OSError, UnicodeError, re.error) as error:
        parser.exit(1, f"regex-extract: {error}\n")


if __name__ == "__main__":
    main()
