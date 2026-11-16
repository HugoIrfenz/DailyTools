# CSV Stack

Append rows from UTF-8 comma-delimited files under one header. Requires Python 3.9+ with no third-party packages.

```bash
printf 'id,name\n1,Ana\n' > first.csv
printf 'name,id\nBudi,2\n' > second.csv
python tools/csv-stack/csv_stack.py first.csv second.csv > combined.csv
```

The final row is `2,Budi`. Files must have the same unique, nonempty column names. Output follows the first file's column order. If a later file or row is invalid, the output may contain earlier rows.
