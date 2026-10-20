# List Compare

Compare membership of two UTF-8 line lists. JSON reports values found only on the left, only on the right, and in both, plus total and unique line counts. Requires Python 3.9+, standard library only.

From the repository root (the first two commands create or overwrite example files):

```bash
printf 'a\nb\n' > before.txt
printf 'b\nc\n' > after.txt
python tools/list-compare/list_compare.py before.txt after.txt --only right
# ["c"] (exit 1)
python tools/list-compare/list_compare.py before.txt after.txt
python -m unittest discover -s tools/list-compare -v
```

`--only left`, `--only right`, or `--only common` emits just that JSON array. Omit it for the full report. One input may be `-` for stdin. Duplicate values are collapsed; left-only/common values retain left first-seen order, right-only values retain right first-seen order. Reordering alone does not change membership.

Each input is limited to 16 MiB and loaded into memory. An initial UTF-8 BOM is removed. LF and CRLF terminate lines; bare CR is retained. Blank lines are empty-string values; a terminating newline does not add an extra value. Spaces, letter case and Unicode normalization are not changed. Output includes the actual list values, JSON-escaped. Exit codes, including with `--only`: 0 same membership, 1 different membership, 2 argument or input error. Source files are not modified.
