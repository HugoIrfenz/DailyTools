# JSON Merge Patch

Apply a JSON Merge Patch document to a target JSON value. Object members are added or replaced, `null` removes an object member, nested objects are merged, and arrays or scalar values are replaced as a whole.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/json-merge-patch/json_merge_patch.py target.json patch.json
cat target.json | python tools/json-merge-patch/json_merge_patch.py - patch.json --compact
python tools/json-merge-patch/json_merge_patch.py target.json patch.json -o result.json
```

For target `{"name":"Ada","active":true}` and patch `{"active":false,"role":"admin"}`, the result is `{"name":"Ada","active":false,"role":"admin"}`.

Input and output are UTF-8. Duplicate object keys, invalid JSON, and non-standard numbers such as `NaN` are rejected. Merge Patch cannot express setting an object member to JSON `null`, because `null` means removal. It does not merge array elements individually. Both inputs are loaded into memory before output is written.

Run the tests:

```bash
python -m unittest discover -s tools/json-merge-patch -p 'test_*.py'
```
