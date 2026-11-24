"""Prefix UTF-8 text lines with consecutive numbers."""
import argparse
import sys
from pathlib import Path


def number_lines(text, start):
    return "".join(f"{number}\t{line}\n"
                   for number, line in enumerate(text.splitlines(), start))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--start", type=int, default=1)
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        output = number_lines(data.decode("utf-8-sig"), args.start)
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, ValueError) as error:
        parser.exit(1, f"line-number: {error}\n")


if __name__ == "__main__":
    main()
