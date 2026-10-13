# Line Unique

Remove duplicate UTF-8 text lines, keeping the first occurrence and its original text in input order.

Requires Python 3.9+. Uses the standard library; no network requests. Run from the repository root:

```bash
python tools/line-unique/line_unique.py items.txt
python tools/line-unique/line_unique.py items.txt --ignore-case --strip --skip-blank
printf 'pear\napple\npear\n' | python tools/line-unique/line_unique.py - --counts
```

The last command produces:

```text
2	pear
1	apple
```

`-` reads stdin. `--counts` adds a count and tab to each retained line. `--stats` writes JSON line counts to stderr. `--strip` and `--ignore-case` change comparisons only; output preserves the first original line. Case comparison uses Unicode casefold.

Output goes to stdout; input files are not modified. Exit codes: `0` for success, `2` for read, UTF-8, or argument errors. Input is fully checked before emitting output.

Limits: LF and CRLF are accepted and output uses LF with a final newline per retained line. Blank lines are retained unless `--skip-blank` is supplied. A UTF-8 BOM is treated as text. Memory grows with distinct lines, so this is not an external-memory deduplicator. Redirect output to a different file; redirecting onto the input path can truncate it before Python starts.

Tests:

```bash
python -m unittest discover -s tools/line-unique -v
```

Checks include nonadjacent duplicates, ordering, counts, Unicode, whitespace, CRLF, empty input, stdin/file CLI, and invalid UTF-8.
