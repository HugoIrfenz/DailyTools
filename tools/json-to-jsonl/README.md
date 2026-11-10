# JSON to JSONL

Convert a top-level JSON array into one compact JSON value per line. Python 3.9+, standard library only. Nested values and decimal number values are retained; whitespace, numeric spelling, and string escaping may change. Non-ASCII characters are escaped in output.

```bash
python tools/json-to-jsonl/json_to_jsonl.py records.json > records.jsonl
printf '[{"id":1},{"id":2}]' | python tools/json-to-jsonl/json_to_jsonl.py -
```

The example emits `{"id":1}` and `{"id":2}` on separate lines. An empty array emits no bytes. UTF-8 input may include a BOM. Duplicate keys, non-standard numbers, malformed JSON, and a non-array root are rejected with exit 1; argument errors use exit 2.

Input and output are held in memory. Deep nesting and very large numbers are subject to Python runtime limits. Output is prepared before writing, so invalid input emits no partial records. Redirect to a different file from the input.

```bash
python -m unittest discover -s tools/json-to-jsonl -v
```
