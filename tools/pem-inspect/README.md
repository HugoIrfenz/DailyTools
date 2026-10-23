# PEM Inspect

Inventory base64-only PEM blocks without parsing their decoded payloads. It reports each label, decoded byte count, SHA-256 digest, line range, and whether another block has the same decoded bytes.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/pem-inspect/pem_inspect.py bundle.pem
cat bundle.pem | python tools/pem-inspect/pem_inspect.py - --json
```

Malformed boundaries, mismatched labels, invalid base64, empty blocks, nested blocks, and non-blank text outside blocks exit with status 1.

The command reads the entire input into memory. It accepts PEM armor containing base64 lines only; legacy encryption headers such as `Proc-Type` are rejected. It does not parse certificates or keys, verify signatures, validate trust, or identify the decoded object beyond its boundary label.

Run the tests:

```bash
python -m unittest discover -s tools/pem-inspect -p 'test_*.py'
```
