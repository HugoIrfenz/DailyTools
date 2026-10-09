# CSV Audit

Check a CSV file before importing it. CSV Audit finds blank or duplicate headers, records with inconsistent column counts, malformed quoting, invalid UTF-8, NUL bytes, and oversized fields—without printing field or header contents.

## Prerequisites

Python 3.9 or newer. No packages to install. Processing is local: the tool reads the input once, does not modify it, and makes no network requests. Run these commands from the repository root; use `python3` if that is your Python command.

## Usage

```bash
python tools/csv-audit/csv_audit.py data.csv
python tools/csv-audit/csv_audit.py data.tsv --delimiter tab
python tools/csv-audit/csv_audit.py rows.csv --no-header --json
```

For stdin on a POSIX shell:

```bash
printf 'id,name\n1,Ada\n' | python tools/csv-audit/csv_audit.py -
```

| Option | Behavior |
| --- | --- |
| `--delimiter CHAR` | Use `comma` (default), `tab`, `semicolon`, `pipe`, `\t`, or one non-quote character. Delimiter detection is deliberately not automatic. |
| `--no-header` | Treat the first record as data and use its width as the expected column count. |
| `--max-errors N` | Keep at most N error details (default 20) while continuing to count all row-width errors. Zero produces counts only. |
| `--max-field-size CHARS` | Set the maximum parsed field length in decoded characters (default 10,000,000). |
| `--json` | Emit a compact, machine-readable JSON report. |

Exit status is `0` for valid input, `1` for invalid CSV, and `2` for an argument or input-read error. Validation reports go to stdout; argument/read errors go to stderr.

## Runnable examples

Audit the included [valid example](examples/valid.csv):

```bash
python tools/csv-audit/csv_audit.py tools/csv-audit/examples/valid.csv
```

```text
OK: 2 data row(s), 3 column(s), 0 error(s), 3 physical line(s); delimiter=comma.
```

The [invalid example](examples/invalid.csv) has a duplicate header and two records with the wrong width:

```bash
python tools/csv-audit/csv_audit.py tools/csv-audit/examples/invalid.csv
```

```text
INVALID: 2 data row(s), 3 column(s), 3 error(s), 3 physical line(s); delimiter=comma.
record 1, line 1, column 3: duplicate_header — header name is duplicated (first seen at column 2)
record 2, line 2: row_width — record has an unexpected number of columns (expected 3, got 2)
record 3, line 3: row_width — record has an unexpected number of columns (expected 3, got 4)
```

JSON output is suitable for CI:

```bash
python tools/csv-audit/csv_audit.py tools/csv-audit/examples/valid.csv --json
```

```json
{"ok":true,"delimiter":",","header_present":true,"column_count":3,"data_row_count":2,"record_count":3,"physical_line_count":3,"error_count":0,"errors":[],"omitted_error_count":0}
```

`record` is the logical CSV record number. `line` is the 1-based physical line where that record ends, so it can be larger than the record number when quoted fields contain newlines. A whole-input `no_records` error uses line `0`.

## Rules and limitations

- Input must be UTF-8. A UTF-8 byte-order mark at the start is accepted. LF and CRLF line endings, quoted delimiters, escaped quotes, quoted newlines, Unicode, and a missing final newline are supported.
- By default, the first logical record is the header. Blank header names and exact duplicate names are errors. Duplicate matching is case-sensitive and does not trim surrounding whitespace. Header names are never included in reports.
- Every data record must have the same field count as the header, or as the first record with `--no-header`. A header-only file is invalid; with `--no-header`, one data record is sufficient.
- Delimiters are explicit because automatic dialect guessing can be ambiguous. The quote character is always the standard double quote (`"`); escape behavior follows Python's `csv` module and doubled quotes.
- Structural checks do not validate data types, required values, business rules, character normalization, spreadsheet formulas, or CSV injection. Empty field values are allowed.
- Invalid UTF-8, NUL bytes, a parser error, or a field exceeding the configured limit stops parsing because the remaining record boundaries may be unreliable. Row-width errors are counted through the entire input.
- Memory usage is bounded by the current parsed record, the largest allowed field, and stored error details rather than total file size. A quoted record may span many physical lines, and a very large record can still consume significant memory.
- Reports omit all source contents, but reveal dimensions and error locations. A mid-stream operating-system read failure exits with status 2 and emits no partial report.

## Checks

```bash
python -m unittest discover -s tools/csv-audit -v
```

Tests cover UTF-8 and BOM input, Unicode, LF/CRLF, quoted delimiters and multiline fields, missing final newlines, empty and header-only files, headerless mode, blank and duplicate headers, ragged rows with continued scanning, capped details, custom delimiters, invalid UTF-8 and NUL bytes, malformed quoting, field-size limits, a 3,000-row single-pass iterator, stdin/file CLI operation, unchanged files, JSON reports, and exit statuses.
