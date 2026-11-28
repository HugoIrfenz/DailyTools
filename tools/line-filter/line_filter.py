"""Keep or exclude logical lines containing a literal substring."""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("substring")
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--ignore-case", action="store_true")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        lines = data.decode("utf-8-sig").splitlines()
        needle = args.substring.casefold() if args.ignore_case else args.substring
        for line in lines:
            candidate = line.casefold() if args.ignore_case else line
            if (needle in candidate) != args.invert:
                sys.stdout.buffer.write((line + "\n").encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"line-filter: {error}\n")


if __name__ == "__main__":
    main()
