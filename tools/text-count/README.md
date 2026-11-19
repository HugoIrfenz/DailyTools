# Text Count

Count bytes, Unicode code points, whitespace-separated words, and logical lines in UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf 'hi\n' | python tools/text-count/text_count.py -
python tools/text-count/text_count.py notes.txt
```

The example reports 3 bytes, 3 code points, 1 word, and 1 line. Lines follow Python's `str.splitlines()` rules, including Unicode line separators. A UTF-8 BOM counts as a code point. The full input is held in memory.
