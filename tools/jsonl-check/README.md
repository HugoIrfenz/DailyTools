# JSONL Check

Validate JSON Lines (`.jsonl` / `.ndjson`) before importing data or processing logs. Find malformed records by line number, including duplicate object keys and non-standard numeric constants, without printing record contents.

## Prerequisites

Python 3.9 or newer. No packages to install. All processing is local; the tool reads its input without modifying it or contacting a network service. Run the commands below from the repository root. Use `python3` if that is your Python command.

## Usage

```bash
python tools/jsonl-check/jsonl_check.py events.jsonl
python tools/jsonl-check/jsonl_check.py events.jsonl --objects-only
python tools/jsonl-check/jsonl_check.py events.jsonl --allow-blank --max-errors 5 --json
```

For stdin on a POSIX shell:

```bash
printf '{"id":1}\n{"id":2}\n' | python tools/jsonl-check/jsonl_check.py -
```

| Option | Behavior |
| --- | --- |
| `--objects-only` | Require every non-blank record to be a JSON object. |
| `--allow-blank` | Skip whitespace-only lines; input must still contain at least one record. |
| `--max-errors N` | Store at most N error details (default 20); scan and count all errors. Zero keeps only counts. |
| `--json` | Emit a machine-readable JSON report instead of text. |

Exit status is `0` for valid input, `1` for invalid input, and `2` for an argument or input-read error. Validation reports go to stdout; argument/read errors go to stderr.

## Runnable examples

The included [valid example](examples/valid.jsonl) has two event objects:

```bash
python tools/jsonl-check/jsonl_check.py tools/jsonl-check/examples/valid.jsonl
```

```text
OK: 2 valid record(s), 0 error(s), 0 blank line(s), 2 line(s) scanned.
```

The [invalid example](examples/invalid.jsonl) has malformed JSON on line 2 and a duplicate `id` key on line 3:

```bash
python tools/jsonl-check/jsonl_check.py tools/jsonl-check/examples/invalid.jsonl
```

```text
INVALID: 1 valid record(s), 2 error(s), 0 blank line(s), 3 line(s) scanned.
line 2, column 17: invalid_json — Expecting value
line 3: duplicate_key — duplicate object key
```

For a JSON report:

```bash
python tools/jsonl-check/jsonl_check.py tools/jsonl-check/examples/valid.jsonl --json
```

```json
{"ok":true,"line_count":2,"valid_record_count":2,"blank_line_count":0,"error_count":0,"errors":[],"omitted_error_count":0}
```

Error details contain `line`, `code`, `message`, and a `column` when the JSON parser supplies one. Line numbers and columns are 1-based; columns count decoded characters, not UTF-8 bytes. A whole-input `no_records` error uses line `0`. Counts cover the entire input even when error details are capped.

## Validation rules and limitations

- Each physical line must contain exactly one JSON value. Objects, arrays, strings, numbers, booleans, and null are accepted unless `--objects-only` is set. Pretty-printed multi-line JSON is not supported.
- Input must be UTF-8 without a byte-order mark. LF and CRLF line endings work; a final newline is optional. Bad UTF-8 on one line does not prevent checking later lines.
- Duplicate object keys are rejected, including nested or escaped-equivalent keys. `NaN`, `Infinity`, and `-Infinity` are rejected. Numeric syntax is checked without converting numbers, so large exponents and long integers do not overflow or get rounded.
- Blank lines are errors by default. Empty input, or blank-only input with `--allow-blank`, fails with `no_records`.
- The tool checks syntax and the rules above, not JSON Schema, field types, required fields, unique records, or application-specific value ranges. It uses Python's JSON string decoding behavior, including acceptance of escaped lone surrogate code points.
- Memory grows with the largest line and its decoded JSON value, plus the capped error details, rather than the full file. There is no hard line-length limit. Excessive nesting is reported as `parser_limit`; a single very large record can exhaust available memory.
- Reports omit keys, values, and source excerpts. They still reveal line counts and error locations. A mid-stream read failure exits with status 2 and emits no partial validation report.

## Checks

```bash
python -m unittest discover -s tools/jsonl-check -v
```

Tests cover all JSON value types, Unicode and CRLF, optional final newlines, empty/blank input, object-only mode, nested duplicates, report privacy, non-standard numbers, huge numeric literals, deep nesting, malformed JSON, BOM and invalid UTF-8, capped errors with continued scanning, a single-pass input iterator, stdin/file CLI operation, unchanged input files, and exit statuses for validation, read, and argument errors.
