# CSV Select

Select and reorder CSV columns by header name. The command validates duplicate headers and inconsistent row widths before writing each row.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/csv-select/csv_select.py people.csv email id
python tools/csv-select/csv_select.py data.tsv name score -d $'\t' -o selected.csv --output-delimiter ,
cat people.csv | python tools/csv-select/csv_select.py - name email
```

Given:

```csv
id,name,email
1,Ada,ada@example.test
```

Selecting `email id` writes:

```csv
email,id
ada@example.test,1
```

Input and output are UTF-8. The first row is always treated as the header. Header matching is exact and case-sensitive. Empty input, duplicate headers, missing columns, duplicate requested columns, malformed CSV, and rows with the wrong field count exit with status 1. Input and output cannot be the same path. Processing is streaming, so an error in a later row can leave earlier output rows already written.

Run the tests:

```bash
python -m unittest discover -s tools/csv-select -p 'test_*.py'
```
