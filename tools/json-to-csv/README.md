# JSON to CSV

Convert a JSON array of flat objects to CSV. Columns are inferred from object keys in first-seen order, or selected explicitly with repeated `--field` options. Missing fields become empty cells; strings, numbers, booleans, and null are supported.

Requires Python 3.9 or newer and has no dependencies.

```bash
python tools/json-to-csv/json_to_csv.py records.json > records.csv
cat records.json | python tools/json-to-csv/json_to_csv.py - --field id --field name
```

Input must be UTF-8, duplicate object keys are rejected, and nested arrays or objects are not flattened. Both the JSON document and converted rows are held in memory. An empty array requires at least one `--field`. Number and boolean formatting follows JSON; null and missing values are both written as empty cells.
