# JSON Flatten

Convert leaves in nested JSON into records containing a JSON Pointer path and the corresponding value. Object keys use JSON Pointer escaping, array positions use numeric path segments, and empty objects or arrays are retained as leaves.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/json-flatten/json_flatten.py data.json
cat data.json | python tools/json-flatten/json_flatten.py - --array
python tools/json-flatten/json_flatten.py data.json -o flat.jsonl
```

Input:

```json
{"users":[{"name":"Ada"}],"active":true}
```

Default JSON Lines output:

```json
{"path":"/users/0/name","value":"Ada"}
{"path":"/active","value":true}
```

Input is UTF-8 and loaded into memory. Duplicate object keys, invalid JSON, and non-standard numbers such as `NaN` are rejected. The output contains leaves only; non-empty intermediate containers are not emitted. A root scalar uses the empty path `""`. `--array` also materializes all output records in memory.

Run the tests:

```bash
python -m unittest discover -s tools/json-flatten -p 'test_*.py'
```
