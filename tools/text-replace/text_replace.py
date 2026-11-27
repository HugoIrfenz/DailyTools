"""Replace literal substrings in UTF-8 text."""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old")
    parser.add_argument("new")
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--count", type=int, help="maximum replacements")
    args = parser.parse_args()
    if not args.old:
        parser.error("old text must be nonempty")
    if args.count is not None and args.count < 0:
        parser.error("count must be nonnegative")
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        text = data.decode("utf-8-sig")
        count = -1 if args.count is None else args.count
        output = text.replace(args.old, args.new, count)
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"text-replace: {error}\n")


if __name__ == "__main__":
    main()
