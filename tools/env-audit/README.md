# Env Audit

Check a local dotenv file against its documented example without printing environment values. Useful before starting an app, reviewing configuration drift, or gating CI.

It reports:

- keys required by the example but missing from the environment;
- environment keys that are not documented in the example;
- empty values;
- duplicate keys;
- invalid variable names and malformed lines.

## Requirements

- Python 3.9 or newer (`python3`, `python`, or `py -3`, depending on your system).
- Standard library only. No installation, account, or network access required.

Run commands from the repository root.

## Quick start

```bash
python tools/env-audit/env_audit.py .env.example .env
```

The tool displays key names and line numbers, but **never displays parsed values**. It reads both files and writes nothing.

Try the safe sample files included in this directory:

```bash
python tools/env-audit/env_audit.py \
  tools/env-audit/examples/.env.example \
  tools/env-audit/examples/.env.sample
```

Expected output:

```text
3 issue(s) found; values were not displayed:
MISSING_KEY .env.sample [LOG_LEVEL]: declared in example but missing from environment
UNEXPECTED_KEY .env.sample:4 [LOCAL_DEBUG]: not declared in example
EMPTY_VALUE .env.sample:3 [API_TOKEN]: value is empty
```

## Options

Allow environment-only keys such as local debugging switches:

```bash
python tools/env-audit/env_audit.py .env.example .env --allow-extra
```

Allow selected keys to be empty; repeat the option for multiple keys:

```bash
python tools/env-audit/env_audit.py .env.example .env \
  --allow-empty OPTIONAL_TOKEN \
  --allow-empty OPTIONAL_REGION
```

Produce a compact JSON report for CI:

```bash
python tools/env-audit/env_audit.py .env.example .env --json
```

Example CI check:

```bash
python tools/env-audit/env_audit.py .env.example .env.ci --json > env-audit-report.json
```

The report contains status and issue metadata only. Protect the report anyway if variable names themselves reveal sensitive architecture.

## Exit codes

- **0:** no issues found.
- **1:** one or more audit issues found.
- **2:** unreadable input, unsupported encoding, or invalid CLI option.

## Parsing rules

- Accepts blank lines, full-line comments, `KEY=VALUE`, and `export KEY=VALUE`.
- Variable names must match `[A-Za-z_][A-Za-z0-9_]*`.
- A blank value, `''`, `""`, or an unquoted comment immediately after `=` is empty.
- Duplicate declarations are reported and the first declaration supplies the line reference.
- Values are treated as opaque text; interpolation, shell execution, and escape expansion never occur.
- Files are read as UTF-8; a leading UTF-8 BOM is accepted.

## Limitations

This is a consistency checker, not a shell or dotenv runtime. It does not resolve `${VARIABLE}` references, validate URLs or credentials, understand multiline values, or determine whether a non-empty value is valid. It intentionally supports portable identifier-style keys only; keys containing dots or hyphens are reported as invalid. The tool reports environment-only keys by default because undocumented configuration drift is often accidental; use `--allow-extra` when it is intentional.

## Verification

```bash
python -m unittest discover -s tools/env-audit -v
```

The suite covers matching files, `export`, missing/unexpected/empty keys, allow lists, duplicate-key redaction, malformed lines, invalid names, comments, BOM/Unicode input, JSON output, exit codes, and missing files.
