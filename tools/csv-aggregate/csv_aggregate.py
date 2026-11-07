#!/usr/bin/env python3
"""Group CSV rows and calculate numeric aggregates."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


class AggregateError(ValueError):
    pass


def _parse_decimal(value: str, column: str, row_number: int) -> Optional[Decimal]:
    if value == "":
        return None
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise AggregateError(f"row {row_number}: column {column!r} is not a decimal") from error
    if not number.is_finite():
        raise AggregateError(f"row {row_number}: column {column!r} must be finite")
    return number


def aggregate_csv(source: str, group_by: Sequence[str], metrics: Sequence[Tuple[str, str]], delimiter: str = ",") -> str:
    if len(delimiter) != 1 or delimiter in "\r\n\"":
        raise AggregateError("delimiter must be one non-newline character other than a quote")
    if len(group_by) != len(set(group_by)):
        raise AggregateError("group-by columns must be unique")
    if len(metrics) != len(set(metrics)):
        raise AggregateError("metric/column pairs must be unique")
    for operation, _ in metrics:
        if operation not in {"sum", "avg", "min", "max"}:
            raise AggregateError(f"unsupported operation {operation!r}")

    try:
        reader = csv.DictReader(source.splitlines(), delimiter=delimiter, strict=True)
        headers = reader.fieldnames
        if not headers:
            raise AggregateError("CSV input must contain a header row")
        if any(not name for name in headers):
            raise AggregateError("CSV headers must not be empty")
        if len(headers) != len(set(headers)):
            raise AggregateError("CSV headers must be unique")
        required = list(group_by) + [column for _, column in metrics]
        missing = [name for name in required if name not in headers]
        if missing:
            raise AggregateError("unknown column(s): " + ", ".join(repr(x) for x in missing))

        groups: "OrderedDict[Tuple[str, ...], Dict[str, object]]" = OrderedDict()
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise AggregateError(f"row {row_number}: field count does not match the header")
            key = tuple(row[name] for name in group_by)
            if key not in groups:
                groups[key] = {"count": 0, "values": {pair: [] for pair in metrics}}
            state = groups[key]
            state["count"] = int(state["count"]) + 1
            values = state["values"]
            for operation, column in metrics:
                number = _parse_decimal(row[column], column, row_number)
                if number is not None:
                    values[(operation, column)].append(number)
    except csv.Error as error:
        raise AggregateError(f"invalid CSV: {error}") from error

    output_headers = list(group_by) + ["count"] + [f"{operation}_{column}" for operation, column in metrics]
    if len(output_headers) != len(set(output_headers)):
        raise AggregateError("generated output column names must be unique")
    from io import StringIO
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    writer.writerow(output_headers)
    for key, state in groups.items():
        row_out: List[str] = list(key) + [str(state["count"])]
        for operation, column in metrics:
            numbers = state["values"][(operation, column)]
            if not numbers:
                row_out.append("")
                continue
            if operation == "sum":
                result = sum(numbers, Decimal(0))
            elif operation == "min":
                result = min(numbers)
            elif operation == "max":
                result = max(numbers)
            else:
                with localcontext() as context:
                    context.prec = 50
                    result = sum(numbers, Decimal(0)) / Decimal(len(numbers))
            row_out.append(format(result, "f"))
        writer.writerow(row_out)
    return buffer.getvalue()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Group CSV rows and calculate numeric aggregates.")
    parser.add_argument("path", nargs="?", default="-", help="CSV file or - for stdin")
    parser.add_argument("--group-by", action="append", default=[], metavar="COLUMN")
    for operation in ("sum", "avg", "min", "max"):
        parser.add_argument(f"--{operation}", action="append", default=[], metavar="COLUMN")
    parser.add_argument("--delimiter", default=",", help="one-character CSV delimiter")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        source = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8-sig")
        metrics = [(operation, column) for operation in ("sum", "avg", "min", "max") for column in getattr(args, operation)]
        sys.stdout.write(aggregate_csv(source, args.group_by, metrics, args.delimiter))
    except (OSError, UnicodeError, AggregateError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
