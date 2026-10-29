# JSON Redact

Replace selected JSON values with a fixed string using JSON Pointer paths. Object members, array elements, escaped `/` and `~` tokens, multiple paths, files, and standard input are supported. Duplicate object keys are rejected.

Requires Python 3.9 or newer and has no dependencies.

```bash
python tools/json-redact/json_redact.py event.json --path /auth/token --path /user/email
cat event.json | python tools/json-redact/json_redact.py - --path /headers/authorization --compact
```

The default replacement is `[REDACTED]`; change it with `--replacement`. Missing paths are errors unless `--ignore-missing` is used. The complete JSON document is loaded into memory, redaction is applied in argument order, and output is written to standard output rather than modifying the source. The tool only replaces explicitly listed paths and does not discover secrets automatically.
