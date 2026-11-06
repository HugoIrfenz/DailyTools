# CSV Diff

Compare two CSV files by one or more key columns. The JSON output lists added and removed rows, changed non-key fields, and summary counts. Row order is ignored.

Requires Python 3.9 or newer and uses only the standard library.

```bash
python tools/csv-diff/csv_diff.py before.csv after.csv --key id
python tools/csv-diff/csv_diff.py before.csv after.csv --key tenant --key id --compact
python tools/csv-diff/csv_diff.py before.csv after.csv --key id --check
```

`--check` exits with status 1 when differences exist. Invalid input exits with status 2. One input path may be `-` to read from stdin.

Both files must have the same unique column names. Key values must be unique within each file. Values are compared as text, the complete files are held in memory, and moved or renamed keys appear as a removal plus an addition.

Run the tests with:

```bash
python -m unittest discover -s tools/csv-diff -p 'test_*.py'
```
