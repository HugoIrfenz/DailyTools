# CSV Unpivot

Turn each non-key column in a wide CSV into a separate row containing the kept keys, original column name, and cell value. Requires Python 3.9+ and uses the standard library.

```bash
printf 'id,jan,feb\na,12,15\n' | python tools/csv-unpivot/csv_unpivot.py --key id
python tools/csv-unpivot/csv_unpivot.py sales.csv --key region --key product > long.csv
```

The first command emits a header of `id,column,value` and rows `a,jan,12` and `a,feb,15`. Input must be comma-delimited UTF-8 with a header. Keys cannot be named `column` or `value`. Blank cells are retained, and an error in a later row can leave partial output.
