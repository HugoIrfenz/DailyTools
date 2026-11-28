# Line Filter

Keep or exclude lines containing a literal substring. Requires Python 3.9+ with no third-party packages.

```bash
printf 'INFO ready\nERROR failed\n' | python tools/line-filter/line_filter.py error - --ignore-case
python tools/line-filter/line_filter.py DEBUG app.log --invert > filtered.txt
```

The example prints `ERROR failed`. Case-insensitive matching uses Unicode casefolding. An empty substring matches every line. Input is UTF-8 with an optional BOM. Lines follow str.splitlines() rules and output uses LF. The full input is held in memory.
