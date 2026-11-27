# Text Replace

Replace literal substrings in UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf 'old old\n' | python tools/text-replace/text_replace.py old new - --count 1
python tools/text-replace/text_replace.py old new notes.txt > changed.txt
```

The example prints `new old`. Matching is case-sensitive and non-overlapping. The default replaces all occurrences. Count zero retains the text. An initial UTF-8 BOM is removed, and other characters and line endings are retained. The full input is held in memory.
