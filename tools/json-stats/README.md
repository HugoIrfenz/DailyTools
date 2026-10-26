# JSON Stats

Summarize a JSON document's root type, node count, maximum depth, value-type counts, object-member counts, and array-item counts. Values and key names are not printed.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/json-stats/json_stats.py response.json
cat response.json | python tools/json-stats/json_stats.py - --json
```

Depth starts at zero for the root value. Empty arrays and objects each count as one node. Input is UTF-8 and loaded into memory. Duplicate object keys, invalid JSON, and non-standard numbers such as `NaN` or `Infinity` are rejected. The summary describes structure only and does not validate a schema.

Run the tests:

```bash
python -m unittest discover -s tools/json-stats -p 'test_*.py'
```
