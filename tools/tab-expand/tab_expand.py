"""Expand tabs to spaces at fixed character-column stops."""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--size", type=int, default=8, help="tab stop spacing, 1 through 256")
    args = parser.parse_args()
    if not 1 <= args.size <= 256:
        parser.error("size must be between 1 and 256")
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        output = data.decode("utf-8-sig").expandtabs(args.size)
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"tab-expand: {error}\n")


if __name__ == "__main__":
    main()
