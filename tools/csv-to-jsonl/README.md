# CSV to JSONL

Convert a header-based CSV file into one JSON object per data row. Header names become object keys and every field remains a string.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/csv-to-jsonl/csv_to_jsonl.py people.csv
python tools/csv-to-jsonl/csv_to_jsonl.py data.tsv -d $'\t' -o data.jsonl
cat people.csv | python tools/csv-to-jsonl/csv_to_jsonl.py -
```

Input:

```csv
id,name
1,Ada
```

Output:

```json
{"id":"1","name":"Ada"}
```

Input is UTF-8. Empty or duplicate header names, malformed CSV, and rows with the wrong field count exit with status 1. Values are not converted to numbers, booleans, or nulls. Processing is streaming, so an error in a later row can leave earlier JSONL records already written. Input and output cannot be the same path.

Run the tests:

```bash
python -m unittest discover -s tools/csv-to-jsonl -p 'test_*.py'
```
