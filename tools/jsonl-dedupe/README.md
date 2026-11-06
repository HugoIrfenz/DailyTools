# JSONL Dedupe

Remove semantic duplicates from JSON Lines input while preserving the order of retained records. By default, complete JSON values are compared after canonical key sorting. One or more JSON Pointers can instead define the identity.

Requires Python 3.9 or newer and uses only the standard library.

```bash
python tools/jsonl-dedupe/jsonl_dedupe.py records.jsonl
python tools/jsonl-dedupe/jsonl_dedupe.py records.jsonl --key /tenant --key /id
cat records.jsonl | python tools/jsonl-dedupe/jsonl_dedupe.py --key /id --keep last --stats
```

`--check` exits with status 1 when duplicates are found. Invalid input exits with status 2. Empty lines are ignored and retained values are emitted as compact JSON.

The complete input is held in memory. JSON Pointer keys must exist in every record. Non-standard JSON numbers such as `NaN` and `Infinity` are rejected.

Run the tests with:

```bash
python -m unittest discover -s tools/jsonl-dedupe -p 'test_*.py'
```
