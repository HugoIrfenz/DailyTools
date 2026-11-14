"""Fill empty CSV cells from the preceding non-empty value in each selected column."""

import argparse
import csv
import sys
from contextlib import nullcontext


def fill_down(source, destination, columns):
    reader = csv.reader(source, strict=True)
    header = next(reader, None)
    if not header:
        raise ValueError("CSV header is required")
    if len(set(header)) != len(header):
        raise ValueError("CSV header contains duplicate names")
    missing = [name for name in columns if name not in header]
    if missing:
        raise ValueError(f"unknown columns: {', '.join(missing)}")

    indexes = [header.index(name) for name in dict.fromkeys(columns)]
    previous = [""] * len(indexes)
    writer = csv.writer(destination)
    writer.writerow(header)
    for row in reader:
        if len(row) != len(header):
            raise ValueError(f"row ending on line {reader.line_num} has {len(row)} fields, expected {len(header)}")
        for slot, index in enumerate(indexes):
            if row[index] == "":
                row[index] = previous[slot]
            else:
                previous[slot] = row[index]
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 CSV file or - for stdin")
    parser.add_argument("--column", action="append", required=True, help="header name, repeatable")
    args = parser.parse_args()
    try:
        if args.input == "-":
            sys.stdin.reconfigure(encoding="utf-8-sig", newline="")
            source = nullcontext(sys.stdin)
        else:
            source = open(args.input, encoding="utf-8-sig", newline="")
        sys.stdout.reconfigure(encoding="utf-8", newline="")
        with source as stream:
            fill_down(stream, sys.stdout, args.column)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"csv-fill-down: {error}\n")


if __name__ == "__main__":
    main()
