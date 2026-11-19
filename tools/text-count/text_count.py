"""Count UTF-8 bytes, Unicode code points, words, and logical lines."""
import argparse
import json
import sys
from pathlib import Path


def count(data):
    text = data.decode("utf-8")
    return {
        "bytes": len(data),
        "code_points": len(text),
        "words": len(text.split()),
        "lines": len(text.splitlines()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        print(json.dumps(count(data)))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"text-count: {error}\n")


if __name__ == "__main__":
    main()
