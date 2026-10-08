#!/usr/bin/env python3
"""Validate JSON Lines locally without printing record contents."""

import argparse
import json
from pathlib import Path
import sys


class RecordError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecordError("duplicate_key", "duplicate object key")
        result[key] = value
    return result


def reject_constant(value):
    raise RecordError("non_json_number", "NaN and Infinity are not JSON numbers")


def validate(lines, allow_blank=False, objects_only=False, max_errors=20):
    """Consume binary lines once; retain at most max_errors issue details."""
    report = {"ok": True, "line_count": 0, "valid_record_count": 0,
              "blank_line_count": 0, "error_count": 0, "errors": []}

    def issue(number, code, message, column=None):
        report["error_count"] += 1
        if len(report["errors"]) < max_errors:
            detail = {"line": number, "code": code, "message": message}
            if column is not None:
                detail["column"] = column
            report["errors"].append(detail)

    for number, raw in enumerate(lines, 1):
        report["line_count"] = number
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError:
            issue(number, "invalid_utf8", "record is not valid UTF-8")
            continue
        if not line.strip():
            report["blank_line_count"] += 1
            if not allow_blank:
                issue(number, "blank_line", "blank lines are not JSON records")
            continue
        try:
            # Check numeric syntax without converting or rounding numeric values.
            value = json.loads(line, parse_float=str, parse_int=str,
                               object_pairs_hook=unique_object,
                               parse_constant=reject_constant)
            if objects_only and not isinstance(value, dict):
                issue(number, "expected_object", "record must be a JSON object")
                continue
        except json.JSONDecodeError as exc:
            # Parser messages and positions contain no record excerpts.
            issue(number, "invalid_json", exc.msg, exc.colno)
            continue
        except RecordError as exc:
            issue(number, exc.code, str(exc))
            continue
        except (ValueError, RecursionError):
            issue(number, "parser_limit", "record exceeds Python parser limits")
            continue
        report["valid_record_count"] += 1

    if not report["valid_record_count"] and not report["error_count"]:
        issue(0, "no_records", "input contains no JSON records")
    report["ok"] = report["error_count"] == 0
    report["omitted_error_count"] = report["error_count"] - len(report["errors"])
    return report


def text_report(report):
    summary = (f"{report['valid_record_count']} valid record(s), "
               f"{report['error_count']} error(s), "
               f"{report['blank_line_count']} blank line(s), "
               f"{report['line_count']} line(s) scanned.")
    lines = [("OK: " if report["ok"] else "INVALID: ") + summary]
    for error in report["errors"]:
        where = f"line {error['line']}" if error["line"] else "input"
        if "column" in error:
            where += f", column {error['column']}"
        lines.append(f"{where}: {error['code']} — {error['message']}")
    if report["omitted_error_count"]:
        lines.append(f"{report['omitted_error_count']} further error(s) omitted from details.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 JSONL/NDJSON file, or '-' for stdin")
    parser.add_argument("--allow-blank", action="store_true", help="skip blank lines")
    parser.add_argument("--objects-only", action="store_true", help="require object records")
    parser.add_argument("--max-errors", type=int, default=20, metavar="N",
                        help="maximum stored error details; full scan continues (default: 20)")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)
    if args.max_errors < 0:
        parser.error("--max-errors must be non-negative")
    try:
        if args.input == "-":
            report = validate(sys.stdin.buffer, args.allow_blank,
                              args.objects_only, args.max_errors)
        else:
            with Path(args.input).open("rb") as handle:
                report = validate(handle, args.allow_blank,
                                  args.objects_only, args.max_errors)
    except OSError:
        print("error: could not read input (check path and permissions)", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, separators=(",", ":"))
          if args.json else text_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
