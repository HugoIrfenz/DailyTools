#!/usr/bin/env python3
"""Transpose a rectangular CSV, treating every row as data."""
import argparse
import csv
import io
import sys
from pathlib import Path


def transpose(text, delimiter=","):
    if len(delimiter) != 1 or delimiter in "\r\n\x00\"":
        raise ValueError("delimiter must be one character other than newline, NUL, or quote")
    if "\x00" in text:
        raise ValueError("NUL bytes are not supported")
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True))
    if not rows:
        return ""
    width = len(rows[0])
    if width == 0:
        raise ValueError("rows must contain at least one field")
    for number, row in enumerate(rows, 1):
        if len(row) != width:
            raise ValueError("inconsistent field count at row " + str(number))
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\r\n")
    writer.writerows(zip(*rows))
    return output.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV file, or - for stdin")
    parser.add_argument("--delimiter", default=",")
    args = parser.parse_args(argv)
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        output = transpose(data.decode("utf-8-sig"), args.delimiter)
        sys.stdout.buffer.write(output.encode("utf-8"))
    except BrokenPipeError:
        return 0
    except (OSError, ValueError, csv.Error) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
