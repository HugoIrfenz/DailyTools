# CSV Transpose

Swap rows and columns in a rectangular CSV. Every row, including a header if present, is treated as data. Python 3.9+, standard library only.

```bash
python tools/csv-transpose/csv_transpose.py matrix.csv > transposed.csv
printf 'name,Ada,Lin\nscore,8,9\n' | python tools/csv-transpose/csv_transpose.py -
python tools/csv-transpose/csv_transpose.py matrix.tsv --delimiter $'\t'
```

The example produces rows `name,score`, `Ada,8`, and `Lin,9`. Quoted delimiters, embedded newlines, empty fields, and Unicode are retained as field values. Output uses UTF-8 without BOM and CRLF record endings; quoting is regenerated.

Input must be UTF-8, optionally with BOM. Empty input emits nothing. Unequal row lengths, blank records, NUL bytes, and quoting errors detected by Python's strict CSV reader return exit 1 without partial output; argument errors use exit 2. Both matrices are held in memory. Redirect to a different file from the input. Formula-like fields are preserved, without spreadsheet formula neutralization.

```bash
python -m unittest discover -s tools/csv-transpose -v
```
