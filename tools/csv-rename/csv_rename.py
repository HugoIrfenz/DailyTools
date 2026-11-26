"""Rename CSV header columns while preserving column order and row values."""
import argparse
import csv
import sys
from contextlib import nullcontext


def rename(source, destination, mappings):
    reader = csv.reader(source, strict=True)
    header = next(reader, None)
    if not header or len(set(header)) != len(header):
        raise ValueError("expected a nonempty header with unique column names")
    missing = set(mappings) - set(header)
    if missing:
        raise ValueError(f"unknown columns: {', '.join(sorted(missing))}")
    renamed = [mappings.get(name, name) for name in header]
    if len(set(renamed)) != len(renamed) or "" in renamed:
        raise ValueError("renamed columns must be nonempty and unique")
    writer = csv.writer(destination)
    writer.writerow(renamed)
    for row in reader:
        if len(row) != len(header):
            raise ValueError(f"line {reader.line_num}: row width differs from header")
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 CSV file or - for stdin")
    parser.add_argument("--rename", nargs=2, action="append", required=True,
                        metavar=("OLD", "NEW"))
    args = parser.parse_args()
    mappings = dict(args.rename)
    if len(mappings) != len(args.rename):
        parser.error("each source column may appear only once")
    try:
        if args.input == "-":
            sys.stdin.reconfigure(encoding="utf-8-sig", newline="")
            source = nullcontext(sys.stdin)
        else:
            source = open(args.input, encoding="utf-8-sig", newline="")
        sys.stdout.reconfigure(encoding="utf-8", newline="")
        with source as stream:
            rename(stream, sys.stdout, mappings)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"csv-rename: {error}\n")


if __name__ == "__main__":
    main()
