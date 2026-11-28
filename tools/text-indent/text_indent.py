"""Prefix logical lines in UTF-8 text."""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--prefix", default="    ")
    parser.add_argument("--skip-blank", action="store_true")
    args = parser.parse_args()
    if "\n" in args.prefix or "\r" in args.prefix:
        parser.error("prefix must not contain CR or LF")
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        for line in data.decode("utf-8-sig").splitlines():
            prefix = "" if args.skip_blank and not line.strip() else args.prefix
            sys.stdout.buffer.write((prefix + line + "\n").encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"text-indent: {error}\n")


if __name__ == "__main__":
    main()
