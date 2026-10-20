# Unicode Inspect

Locate characters in Unicode categories `Cc` (control), `Cf` (format), and `Zs`/`Zl`/`Zp` (separators), except ordinary space, tab, CR, and LF. Reports code point, category, name, and position rather than surrounding input text. Requires Python 3.9+, standard library only.

From the repository root:

```bash
python -c "import sys; sys.stdout.buffer.write('a\u200bb'.encode('utf-8'))" | python tools/unicode-inspect/unicode_inspect.py
# Matches: 1 (Unicode version depends on Python)
# 1:2 U+200B Cf ZERO WIDTH SPACE
python tools/unicode-inspect/unicode_inspect.py source.txt --json --limit 20
python -m unittest discover -s tools/unicode-inspect -v
```

Input defaults to stdin (`-`), must be UTF-8, and is limited to 16 MiB in memory. An initial BOM is reported, not stripped. Positions are one-based; only LF advances the line, and every code point (including tabs) advances one column. Columns are not display widths or grapheme positions. `--limit` bounds individual findings (0–10000, default 100), not total scanning or per-code-point counts. JSON includes totals, omitted count, counts, and the runtime Unicode database version.

This is a category filter, not a comprehensive invisible-character, confusable, or source-code validator. For example, combining marks and variation selectors are not selected. Detection depends on Python's Unicode database; no changes are made to input files. Exit codes: 0 no matches, 1 matches (even with `--limit 0`), 2 argument or input error.
