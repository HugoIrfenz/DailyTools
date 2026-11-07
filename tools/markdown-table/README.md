# Markdown Table

Align GitHub-flavored Markdown pipe tables by column width while retaining left, center, or right alignment markers. Pipes escaped with a backslash or enclosed in matching inline-code backticks are treated as cell content.

Requires Python 3.9 or newer and uses only the standard library.

```bash
python tools/markdown-table/markdown_table.py README.md
cat notes.md | python tools/markdown-table/markdown_table.py
```

Only tables with a header followed by a valid pipe-table separator are formatted. A row with a different number of columns is reported as an error. Formatting normalizes line endings to LF.

Run tests with:

```bash
python -m unittest discover -s tools/markdown-table -p 'test_*.py'
```
