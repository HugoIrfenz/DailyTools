# Text Indent

Prefix each logical text line, with four spaces by default. Requires Python 3.9+ with no third-party packages.

```bash
printf 'hello\nworld' | python tools/text-indent/text_indent.py - --prefix '> '
python tools/text-indent/text_indent.py snippet.txt --skip-blank > indented.txt
```

The example prints `> hello` and `> world`. Skip-blank leaves whitespace-only lines without the prefix. Input is UTF-8 with an optional BOM. Lines follow str.splitlines() rules and output terminates each line with LF. The full input is held in memory.
