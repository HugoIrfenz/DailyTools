# JSON Select

Extract a value from JSON using an array of string keys and non-negative integer indexes. Requires Python 3.9+; standard library only, no network requests.

From the repository root:

```bash
python tools/json-select/json_select.py response.json '["users",0,"name"]'
printf '{"users":[{"name":"Ada"}]}' | python tools/json-select/json_select.py - '["users",0,"name"]'
```

The second command outputs `"Ada"`. `[]` selects the document root. A string such as `"0"` selects an object key; integer `0` selects an array element. Dots, slashes and empty keys have no special syntax.

Output is JSON, with numbers decoded as Decimal and emitted without float conversion; formatting may change. Exit `0` means found (including null/false), `1` means missing or incompatible path, `2` means input, parser, or argument error. Files are unchanged.

Limits: the input byte limit defaults to 16 MiB (`--max-bytes` overrides it). Parsing holds the document in memory and is subject to Python/Decimal nesting and numeric limits. UTF-8 is required; duplicate object keys and NaN/Infinity are rejected. This is not JSONPath: no wildcards, filters, or negative indexes.

Tests: `python -m unittest discover -s tools/json-select -v` covers nested selection, special keys, exact numbers, missing/null distinction, limits, and file/stdin CLI.
