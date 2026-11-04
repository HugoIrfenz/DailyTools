# TOML Inspect

Lists TOML table paths, key names, value types, and array lengths without printing values. Arrays of tables are expanded into indexed table paths. JSON is the default output; `--text` writes a compact report.

Requires Python 3.11 or newer. It has no third-party dependencies.

```bash
python tools/toml-inspect/toml_inspect.py pyproject.toml
cat config.toml | python tools/toml-inspect/toml_inspect.py - --text
```

UTF-8 input with or without a BOM is accepted. Invalid TOML and duplicate keys are rejected. Key names and table paths are included in output. The complete file is parsed in memory according to Python's `tomllib` behavior.

```bash
python -m unittest discover -s tools/toml-inspect -p 'test_*.py'
```
