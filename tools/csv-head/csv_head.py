"""Print a CSV header and the first N data records."""
import argparse
import csv
import sys
from contextlib import nullcontext
from itertools import islice


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 CSV file or - for stdin")
    parser.add_argument("--rows", type=int, default=10)
    args = parser.parse_args()
    if args.rows < 0:
        parser.error("rows must be nonnegative")
    try:
        if args.input == "-":
            sys.stdin.reconfigure(encoding="utf-8-sig", newline="")
            source = nullcontext(sys.stdin)
        else:
            source = open(args.input, encoding="utf-8-sig", newline="")
        sys.stdout.reconfigure(encoding="utf-8", newline="")
        with source as stream:
            reader = csv.reader(stream, strict=True)
            writer = csv.writer(sys.stdout)
            header = next(reader, None)
            if header is not None:
                writer.writerow(header)
                writer.writerows(islice(reader, args.rows))
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"csv-head: {error}\n")


if __name__ == "__main__":
    main()
