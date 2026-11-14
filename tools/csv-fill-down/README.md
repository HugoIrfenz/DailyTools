# CSV Fill Down

Fill empty cells in selected columns with the last non-empty value in the same column. Requires Python 3.9+ with no third-party packages.

```bash
printf 'team,name\nPlatform,Ana\n,Budi\n' | python tools/csv-fill-down/csv_fill_down.py - --column team
python tools/csv-fill-down/csv_fill_down.py report.csv --column team --column region > filled.csv
```

The first command prints `Platform,Budi` for the second data row. Input is UTF-8 comma-delimited CSV with a header. Leading empty cells stay empty, and whitespace counts as a value. Each column carries forward across the entire file. Output may contain earlier rows if a later row fails validation.
