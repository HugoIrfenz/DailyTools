#!/usr/bin/env python3
"""Audit a dotenv file against an example without exposing variable values."""

import argparse
import json
from pathlib import Path
import re
import sys


KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def visible_path(path):
    """Avoid leaking full local paths in reports."""
    return Path(path).name


def parse_dotenv(path):
    """Return key metadata and parser issues for a UTF-8 dotenv file."""
    source = Path(path)
    text = source.read_text(encoding="utf-8-sig")
    keys = {}
    issues = []

    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        candidate = stripped
        if candidate.startswith("export") and len(candidate) > 6 and candidate[6].isspace():
            candidate = candidate[6:].lstrip()

        if "=" not in candidate:
            issues.append({"code": "invalid_line", "file": visible_path(path),
                           "line": number, "message": "expected KEY=VALUE"})
            continue

        key, raw_value = candidate.split("=", 1)
        key = key.strip()
        if not KEY_RE.fullmatch(key):
            issues.append({"code": "invalid_key", "file": visible_path(path),
                           "line": number, "message": "invalid variable name"})
            continue

        if key in keys:
            issues.append({"code": "duplicate_key", "file": visible_path(path),
                           "line": number, "key": key,
                           "message": f"first declared on line {keys[key]['line']}"})
            continue

        keys[key] = {"line": number, "empty": is_empty(raw_value)}

    return keys, issues


def is_empty(raw_value):
    value = raw_value.strip()
    if not value:
        return True
    if value in ("''", '\"\"'):
        return True
    # An unquoted inline comment after '=' contains no value.
    if value.startswith("#"):
        return True
    return False


def audit(example_path, env_path, allow_extra=False, allowed_empty=()):
    expected, issues = parse_dotenv(example_path)
    actual, actual_issues = parse_dotenv(env_path)
    issues.extend(actual_issues)
    allowed_empty = set(allowed_empty)

    for key in sorted(expected.keys() - actual.keys()):
        issues.append({"code": "missing_key", "file": visible_path(env_path),
                       "key": key, "message": "declared in example but missing from environment"})

    if not allow_extra:
        for key in sorted(actual.keys() - expected.keys()):
            issues.append({"code": "unexpected_key", "file": visible_path(env_path),
                           "line": actual[key]["line"], "key": key,
                           "message": "not declared in example"})

    for key in sorted(actual.keys() & expected.keys()):
        if actual[key]["empty"] and key not in allowed_empty:
            issues.append({"code": "empty_value", "file": visible_path(env_path),
                           "line": actual[key]["line"], "key": key,
                           "message": "value is empty"})

    return issues, len(expected), len(actual)


def format_text(issues, expected_count, actual_count):
    if not issues:
        return f"OK: {actual_count} environment key(s) match the {expected_count}-key example."
    lines = [f"{len(issues)} issue(s) found; values were not displayed:"]
    for issue in issues:
        location = issue["file"]
        if "line" in issue:
            location += f":{issue['line']}"
        key = f" [{issue['key']}]" if "key" in issue else ""
        lines.append(f"{issue['code'].upper()} {location}{key}: {issue['message']}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", help="reference dotenv file, usually .env.example")
    parser.add_argument("environment", help="dotenv file to audit, usually .env")
    parser.add_argument("--allow-extra", action="store_true",
                        help="do not report keys absent from the example")
    parser.add_argument("--allow-empty", action="append", default=[], metavar="KEY",
                        help="permit an empty value for KEY (repeatable)")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args(argv)

    invalid_allowed = [key for key in args.allow_empty if not KEY_RE.fullmatch(key)]
    if invalid_allowed:
        print(f"error: invalid --allow-empty key: {invalid_allowed[0]!r}", file=sys.stderr)
        return 2

    try:
        issues, expected_count, actual_count = audit(
            args.example, args.environment, args.allow_extra, args.allow_empty
        )
    except (OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"ok": not issues, "issue_count": len(issues),
                          "expected_key_count": expected_count,
                          "actual_key_count": actual_count, "issues": issues},
                         ensure_ascii=False, separators=(",", ":")))
    else:
        print(format_text(issues, expected_count, actual_count))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
