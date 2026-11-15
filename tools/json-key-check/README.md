# JSON Key Check

Report duplicate object members in UTF-8 JSON, including objects nested inside arrays. Requires Python 3.9+ with no third-party packages.

```bash
printf '%s\n' '{"rows":[{"id":1,"id":2}]}' | python tools/json-key-check/json_key_check.py -
python tools/json-key-check/json_key_check.py config.json
```

The first command prints `["rows", 0, "id"]`. Each occurrence after the first prints a path made of object keys and array indexes. Repeated parent keys can produce identical paths. Exit status is 0 for clean input, 1 for duplicates, and 2 for input errors. The full document is decoded in memory.
