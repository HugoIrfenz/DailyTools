"""Reverse the order of logical lines in UTF-8 text."""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        lines = data.decode("utf-8-sig").splitlines()
        output = "\n".join(reversed(lines)) + ("\n" if lines else "")
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"line-reverse: {error}\n")


if __name__ == "__main__":
    main()
