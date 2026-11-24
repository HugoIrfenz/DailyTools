# Line Number

Prefix every logical text line with a number and a tab. Requires Python 3.9+ with no third-party packages.

```bash
printf 'alpha\nbeta' | python tools/line-number/line_number.py - --start 10
python tools/line-number/line_number.py notes.txt > numbered.txt
```

The example prints `10<TAB>alpha` and `11<TAB>beta`. Blank lines are numbered. Input is UTF-8 with an optional BOM. Lines follow Python's `str.splitlines()` rules, including Unicode separators. Output uses LF and ends each numbered line with LF. The full input is held in memory.
