# Tab Expand

Expand tabs to spaces at fixed character-column stops in UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf 'a\tb\n' | python tools/tab-expand/tab_expand.py - --size 4
python tools/tab-expand/tab_expand.py source.txt --size 4 > expanded.txt
```

The example places three spaces between `a` and `b`. Tab spacing defaults to 8 and accepts 1 through 256. CR and LF reset the column counter. Width follows Python's `str.expandtabs()`, counting each Unicode code point as one column. An initial BOM is removed. Other characters and line endings are retained. The full input is held in memory.
