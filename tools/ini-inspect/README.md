# INI Inspect

Lists INI section names and explicit key names without printing their values. JSON output reports default keys, section order, per-section key counts, and a total count. `--text` writes the same inventory as plain text.

Requires Python 3.9 or newer. It has no third-party dependencies.

```bash
python tools/ini-inspect/ini_inspect.py config.ini
cat config.ini | python tools/ini-inspect/ini_inspect.py - --text
```

Key case and source order are preserved. Duplicate sections, duplicate keys with the same case, missing section headers, invalid syntax, and invalid UTF-8 are rejected. The complete file is read into memory. The parser follows Python's `configparser` INI rules; it is not a validator for every application-specific INI dialect.

Run the tests with:

```bash
python -m unittest discover -s tools/ini-inspect -p 'test_*.py'
```
