# CSV Sort

Sorts header-based CSV rows by one or more named columns. Comparisons can use text, case-folded text, or finite decimal numbers. Sorting is stable, and `--reverse` applies descending order to every selected key.

Requires Python 3.9 or newer. It has no third-party dependencies.

```bash
python tools/csv-sort/csv_sort.py people.csv --key country --key name
cat scores.csv | python tools/csv-sort/csv_sort.py - --key score --numeric --reverse
```

Headers must be unique and non-empty, and all rows must have the header's field count. The output rewrites CSV quoting and line endings rather than preserving the original byte representation. Numeric mode applies to every sort key and rejects empty, invalid, or non-finite values. The complete CSV is held in memory.

Run the tests with:

```bash
python -m unittest discover -s tools/csv-sort -p 'test_*.py'
```
