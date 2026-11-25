# Text Dedent

Remove common leading whitespace from UTF-8 text using Python's textwrap module. Requires Python 3.9+ with no third-party packages.

```bash
printf '    alpha\n      beta\n' | python tools/text-dedent/text_dedent.py -
python tools/text-dedent/text_dedent.py snippet.txt > dedented.txt
```

The example removes four leading spaces from each line. Tabs and spaces are distinct when finding the common prefix. Whitespace-only lines are normalized. CRLF and CR become LF, and an initial BOM is removed. The full input is held in memory.
