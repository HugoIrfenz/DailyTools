#!/usr/bin/env python3
"""Audit CSV structure locally without printing field contents."""

import argparse
import csv
import json
from pathlib import Path
import sys


DELIMITERS = {"comma": ",", "tab": "\t", "semicolon": ";", "pipe": "|"}


class InputIssue(Exception):
    def __init__(self, line, code, message):
        super().__init__(message)
        self.line = line
        self.code = code


class DecodedLines:
    """Decode a binary line iterator while tracking physical line numbers."""

    def __init__(self, lines):
        self.lines = iter(lines)
        self.line_count = 0

    def __iter__(self):
        return self

    def __next__(self):
        raw = next(self.lines)
        self.line_count += 1
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InputIssue(self.line_count, "invalid_utf8",
                             "physical line is not valid UTF-8") from exc
        if self.line_count == 1 and text.startswith("\ufeff"):
            text = text[1:]
        if "\x00" in text:
            raise InputIssue(self.line_count, "nul_byte",
                             "NUL bytes are not supported in CSV input")
        return text


def validate(lines, delimiter=",", header=True, max_errors=20,
             max_field_size=10_000_000):
    """Consume binary lines once and return a content-safe audit report."""
    decoded = DecodedLines(lines)
    reader = csv.reader(decoded, delimiter=delimiter, strict=True)
    report = {
        "ok": True,
        "delimiter": delimiter,
        "header_present": header,
        "column_count": 0,
        "data_row_count": 0,
        "record_count": 0,
        "physical_line_count": 0,
        "error_count": 0,
        "errors": [],
    }

    def issue(code, message, **details):
        report["error_count"] += 1
        if len(report["errors"]) < max_errors:
            report["errors"].append({"code": code, "message": message, **details})

    old_limit = csv.field_size_limit()
    csv.field_size_limit(max_field_size)
    expected = None
    try:
        for record_number, row in enumerate(reader, 1):
            report["record_count"] = record_number
            end_line = reader.line_num
            if record_number == 1:
                expected = len(row)
                report["column_count"] = expected
                if header:
                    first_seen = {}
                    for column, name in enumerate(row, 1):
                        if not name.strip():
                            issue("blank_header", "header name is blank",
                                  record=record_number, line=end_line, column=column)
                        if name in first_seen:
                            issue("duplicate_header", "header name is duplicated",
                                  record=record_number, line=end_line, column=column,
                                  first_column=first_seen[name])
                        else:
                            first_seen[name] = column
                    continue
            report["data_row_count"] += 1
            if len(row) != expected:
                issue("row_width", "record has an unexpected number of columns",
                      record=record_number, line=end_line,
                      expected=expected, actual=len(row))
    except InputIssue as exc:
        issue(exc.code, str(exc), line=exc.line)
    except csv.Error as exc:
        issue("invalid_csv", str(exc), line=decoded.line_count)
    finally:
        csv.field_size_limit(old_limit)
        report["physical_line_count"] = decoded.line_count

    if not report["record_count"] and not report["error_count"]:
        issue("no_records", "input contains no CSV records", line=0)
    elif header and report["record_count"] == 1 and not report["error_count"]:
        issue("no_data_rows", "input contains a header but no data rows", line=reader.line_num)

    report["ok"] = report["error_count"] == 0
    report["omitted_error_count"] = report["error_count"] - len(report["errors"])
    return report


def text_report(report):
    delimiter = {",": "comma", "\t": "tab", ";": "semicolon", "|": "pipe"}.get(
        report["delimiter"], repr(report["delimiter"]))
    summary = (f"{report['data_row_count']} data row(s), "
               f"{report['column_count']} column(s), "
               f"{report['error_count']} error(s), "
               f"{report['physical_line_count']} physical line(s); delimiter={delimiter}.")
    lines = [("OK: " if report["ok"] else "INVALID: ") + summary]
    for error in report["errors"]:
        places = []
        if error.get("record") is not None:
            places.append(f"record {error['record']}")
        if error.get("line") is not None:
            places.append("input" if error["line"] == 0 else f"line {error['line']}")
        if error.get("column") is not None:
            places.append(f"column {error['column']}")
        prefix = ", ".join(places) + ": " if places else ""
        suffix = ""
        if error["code"] == "row_width":
            suffix = f" (expected {error['expected']}, got {error['actual']})"
        elif error["code"] == "duplicate_header":
            suffix = f" (first seen at column {error['first_column']})"
        lines.append(f"{prefix}{error['code']} — {error['message']}{suffix}")
    if report["omitted_error_count"]:
        lines.append(f"{report['omitted_error_count']} further error(s) omitted from details.")
    return "\n".join(lines)


def delimiter_value(value):
    if value in DELIMITERS:
        return DELIMITERS[value]
    if value == r"\t":
        return "\t"
    if len(value) == 1 and value not in "\r\n\"":
        return value
    raise argparse.ArgumentTypeError(
        "delimiter must be comma, tab, semicolon, pipe, \\t, or one non-quote character")


def positive_integer(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def nonnegative_integer(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 CSV file, or '-' for stdin")
    parser.add_argument("--delimiter", type=delimiter_value, default=",", metavar="CHAR",
                        help="comma, tab, semicolon, pipe, \\t, or one character")
    parser.add_argument("--no-header", action="store_true",
                        help="treat the first record as data")
    parser.add_argument("--max-errors", type=nonnegative_integer, default=20, metavar="N",
                        help="stored error details; full row scan continues (default: 20)")
    parser.add_argument("--max-field-size", type=positive_integer, default=10_000_000,
                        metavar="CHARS", help="parser field limit (default: 10000000)")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            report = validate(sys.stdin.buffer, args.delimiter, not args.no_header,
                              args.max_errors, args.max_field_size)
        else:
            with Path(args.input).open("rb") as handle:
                report = validate(handle, args.delimiter, not args.no_header,
                                  args.max_errors, args.max_field_size)
    except OSError:
        print("error: could not read input (check path and permissions)", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, separators=(",", ":"))
          if args.json else text_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
