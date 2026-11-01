# CSV Frequency

Counts values in selected CSV columns and orders them by descending count, then value. JSON output includes the total row count, distinct count, and the most frequent values. Empty strings are counted unless `--ignore-empty` is used.

Requires Python 3.9 or newer. It has no third-party dependencies.

```bash
python tools/csv-frequency/csv_frequency.py data.csv --column status --top 20
cat data.csv | python tools/csv-frequency/csv_frequency.py - --column country --ignore-empty
python tools/csv-frequency/csv_frequency.py data.csv --tsv
```

The first row must contain unique, non-empty headers and every data row must have the same field count. Values remain strings. The utility reads the complete CSV into memory and does not infer numeric or date types.

Run the tests with:

```bash
python -m unittest discover -s tools/csv-frequency -p 'test_*.py'
```
