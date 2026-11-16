"""Stack CSV files and align columns by header name."""
import argparse
import csv
import sys


def stack(paths, output):
    writer = csv.writer(output)
    schema = None
    for path in paths:
        with open(path, encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            try:
                header = next(reader, [])
                if not header or "" in header or len(set(header)) != len(header):
                    raise ValueError("expected a header with unique, nonempty names")
                if schema is None:
                    schema = header
                    writer.writerow(schema)
                if set(header) != set(schema):
                    raise ValueError("column names differ from the first file")
                positions = {name: index for index, name in enumerate(header)}
                indexes = [positions[name] for name in schema]
                for row in reader:
                    if len(row) != len(header):
                        raise ValueError("row width differs from the header")
                    writer.writerow([row[index] for index in indexes])
            except (ValueError, csv.Error) as error:
                raise ValueError(f"{path}, line {reader.line_num}: {error}") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", newline="")
    try:
        stack(args.files, sys.stdout)
    except (OSError, ValueError) as error:
        parser.exit(1, f"csv-stack: {error}\n")


if __name__ == "__main__":
    main()
