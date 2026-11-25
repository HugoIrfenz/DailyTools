# Line Reverse

Reverse the order of logical lines in UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf 'first\nsecond' | python tools/line-reverse/line_reverse.py -
python tools/line-reverse/line_reverse.py entries.txt > reversed.txt
```

The example prints `second` then `first`. Blank lines are retained. Line splitting follows Python's str.splitlines(), including Unicode separators. Output uses LF and terminates each line with LF. An initial BOM is removed. The full input is held in memory.
