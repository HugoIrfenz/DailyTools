# JSONL to JSON

Converts non-empty JSON Lines records into one JSON array. Blank lines are ignored by default and can be rejected with `--reject-blank`. Duplicate object keys, non-standard numeric constants, non-finite numbers, invalid JSON, and invalid UTF-8 are rejected with line details.

Requires Python 3.9 or newer. It has no third-party dependencies.

```bash
python tools/jsonl-to-json/jsonl_to_json.py records.jsonl
cat records.jsonl | python tools/jsonl-to-json/jsonl_to_json.py - --indent 2
```

Every non-empty line must contain one complete JSON value. Records are not required to be objects. The complete input and output array are held in memory.

```bash
python -m unittest discover -s tools/jsonl-to-json -p 'test_*.py'
```
