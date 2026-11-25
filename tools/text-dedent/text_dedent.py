"""Remove common leading whitespace from UTF-8 text."""
import argparse
import sys
import textwrap
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        sys.stdout.buffer.write(textwrap.dedent(text).encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"text-dedent: {error}\n")


if __name__ == "__main__":
    main()
