# Text Wrap

Wrap whitespace-separated paragraphs to a chosen width. Requires Python 3.9+ with no third-party packages.

```bash
printf 'one two three four\n' | python tools/text-wrap/text_wrap.py - --width 9
python tools/text-wrap/text_wrap.py notes.txt --width 72 > wrapped.txt
```

The example prints `one two`, `three`, and `four` on separate lines. Blank lines separate paragraphs. Input whitespace is collapsed, and nonempty output ends with LF. Long words remain intact and can exceed the width. Width counts Unicode code points. The full input is held in memory.
