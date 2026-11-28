# CSV Head

Print a CSV header and the first N data records. Requires Python 3.9+ with no third-party packages.

```bash
python tools/csv-head/csv_head.py report.csv --rows 5
printf 'id,name\n1,Ana\n2,Budi\n' | python tools/csv-head/csv_head.py - --rows 1
```

The example prints the header and Ana's record. Quoted multiline values count as one record. Input is UTF-8 comma-delimited CSV with an optional BOM. Output uses CSV quoting and CRLF. Only selected records are parsed. A parsing error may leave earlier output.
