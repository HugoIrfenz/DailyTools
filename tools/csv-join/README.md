# CSV Join

Join two CSV files by named key columns. Inner, left, and full joins are supported. Duplicate keys produce all matching row combinations. The right key is omitted from output; colliding right-side column names receive a `right.` prefix.

Requires Python 3.9 or newer and has no dependencies.

```bash
python tools/csv-join/csv_join.py users.csv scores.csv --left-key id
python tools/csv-join/csv_join.py users.csv orders.csv --left-key id --right-key user_id --how left > joined.csv
```

Both inputs must use the same one-character delimiter, selected with `--delimiter` when it is not a comma. Files are decoded as UTF-8 with an optional BOM. Headers must be unique and every row must match its header width. Both files are loaded into memory; key comparison is exact and string-based. Full joins place an unmatched right key in the left key column.
