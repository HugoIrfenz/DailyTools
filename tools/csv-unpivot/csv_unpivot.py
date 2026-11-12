import argparse
import csv
import io
import sys
from contextlib import nullcontext


def unpivot(source, output, keys):
    reader = csv.reader(source, strict=True)
    header = next(reader, [])
    if not header or "" in header or len(set(header)) != len(header):
        raise ValueError("expected unique, nonempty column names")
    if len(set(keys)) != len(keys) or any(key not in header for key in keys):
        raise ValueError("key columns must exist and be specified only once")
    if {"column", "value"}.intersection(keys):
        raise ValueError("key names cannot be 'column' or 'value'")
    key_indices = [header.index(key) for key in keys]
    values = [(index, name) for index, name in enumerate(header) if name not in keys]
    if not values:
        raise ValueError("expected at least one non-key column")
    writer = csv.writer(output)
    writer.writerow([*keys, "column", "value"])
    for row in reader:
        if len(row) != len(header):
            raise ValueError(f"row ending at line {reader.line_num}: expected {len(header)} fields")
        key_values = [row[index] for index in key_indices]
        for index, name in values:
            writer.writerow([*key_values, name, row[index]])


def main():
    parser = argparse.ArgumentParser(description="Turn wide CSV columns into name/value rows.")
    parser.add_argument("file", nargs="?", default="-", help="UTF-8 CSV file or - for stdin")
    parser.add_argument("--key", action="append", required=True, help="Column to keep, repeatable")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", newline="")
    try:
        source = (
            nullcontext(io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig", newline=""))
            if args.file == "-"
            else open(args.file, encoding="utf-8-sig", newline="")
        )
        with source as stream:
            unpivot(stream, sys.stdout, args.key)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
