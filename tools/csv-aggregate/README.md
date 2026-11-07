# CSV Aggregate

Group CSV rows by one or more columns and calculate count, sum, average, minimum, or maximum for selected numeric columns. Groups are emitted in first-seen order; blank numeric cells are ignored by numeric operations.

Requires Python 3.9 or newer and uses only the standard library.

```bash
python tools/csv-aggregate/csv_aggregate.py sales.csv --group-by region --sum amount --avg amount
cat sales.csv | python tools/csv-aggregate/csv_aggregate.py --group-by region --group-by product --sum amount
```

Without `--group-by`, the input is aggregated as one group. Numeric values use decimal arithmetic; non-finite or invalid values are rejected. The input is held in memory.

Run tests with:

```bash
python -m unittest discover -s tools/csv-aggregate -p 'test_*.py'
```
