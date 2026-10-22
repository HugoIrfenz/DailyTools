# UUID Inspect

Normalize UUID text and display its canonical form, hexadecimal value, URN, integer, variant, version, and nil/max flags. It can also require an expected version.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/uuid-inspect/uuid_inspect.py 550e8400-e29b-41d4-a716-446655440000
printf '%s\n' 550e8400-e29b-41d4-a716-446655440000 | python tools/uuid-inspect/uuid_inspect.py --json
python tools/uuid-inspect/uuid_inspect.py 550e8400-e29b-41d4-a716-446655440000 --require-version 4
```

Multiple arguments or non-empty stdin lines are accepted. `--json` returns an array. Invalid input or a `--require-version` mismatch exits with status 1.

The parser accepts the forms supported by Python's `uuid.UUID`, including canonical hyphenated text, braces, URNs, and 32 hexadecimal digits. The tool reports encoded fields only; it does not establish where a UUID came from, whether it is unique, or whether embedded data is trustworthy.

Run the tests:

```bash
python -m unittest discover -s tools/uuid-inspect -p 'test_*.py'
```
