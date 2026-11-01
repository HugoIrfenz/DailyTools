# JSON Canonicalize

Sorts object keys recursively and writes JSON as compact text or with a selected indentation width. Duplicate object keys, non-standard numeric constants, non-finite floats, invalid JSON, and invalid UTF-8 are rejected.

Requires Python 3.9 or newer. It has no third-party dependencies.

```bash
python tools/json-canonicalize/json_canonicalize.py input.json
cat input.json | python tools/json-canonicalize/json_canonicalize.py - --indent 2
python tools/json-canonicalize/json_canonicalize.py input.json --ascii
```

The output is deterministic for the same parsed values on the same Python runtime. This is not an implementation of RFC 8785: number formatting follows Python's JSON encoder, and keys are ordered by Python string order.

Run the tests with:

```bash
python -m unittest discover -s tools/json-canonicalize -p 'test_*.py'
```
