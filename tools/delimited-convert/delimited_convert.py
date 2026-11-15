"""Convert quoted text records between comma, tab, semicolon, and pipe delimiters."""
import argparse
import csv
import sys
from contextlib import nullcontext


DELIMITERS = {"comma": ",", "tab": "\t", "semicolon": ";", "pipe": "|"}


def convert(source, destination, input_delimiter, output_delimiter):
    reader = csv.reader(source, delimiter=input_delimiter, strict=True)
    writer = csv.writer(destination, delimiter=output_delimiter)
    writer.writerows(reader)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--from", dest="source", choices=DELIMITERS, required=True)
    parser.add_argument("--to", choices=DELIMITERS, required=True)
    args = parser.parse_args()
    try:
        if args.input == "-":
            sys.stdin.reconfigure(encoding="utf-8-sig", newline="")
            source = nullcontext(sys.stdin)
        else:
            source = open(args.input, encoding="utf-8-sig", newline="")
        sys.stdout.reconfigure(encoding="utf-8", newline="")
        with source as stream:
            convert(stream, sys.stdout, DELIMITERS[args.source], DELIMITERS[args.to])
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"delimited-convert: {error}\n")


if __name__ == "__main__":
    main()
