# EOL Inspect

Count LF, CRLF and bare CR endings in a file. Reports byte and logical-line counts, mixed endings, and whether the input ends with a newline. Python 3.9+; standard library only.

From the repository root:

```bash
python tools/eol-inspect/eol_inspect.py source.py --json
printf 'a\r\nb\n' | python tools/eol-inspect/eol_inspect.py - --check
```

The second command reports one CRLF and one LF and exits `1`. With `--check`, mixed endings or a nonempty file without a final newline fail. Empty files pass. Without `--check`, inspection exits `0`; read/argument errors exit `2`.

Files are read in 1 MiB chunks and not modified. No text decoding is performed: binary files are accepted, and CR/LF bytes are counted literally. A trailing non-newline segment counts as one line. Unicode line separators and UTF-16 text are not interpreted.

Tests: `python -m unittest discover -s tools/eol-inspect -v` checks all three endings, chunk boundaries, binary input, empty files, final newlines, and CLI exit codes.
