# Regex Extract

Extract Python regular expression matches from UTF-8 text as JSON Lines. Requires Python 3.9+ with no third-party packages.

```bash
printf 'order=42 order=73' | python tools/regex-extract/regex_extract.py 'order=(?P<id>[0-9]+)' -
python tools/regex-extract/regex_extract.py 'error[^\n]*' app.log --ignore-case
```

Each record includes the full match, capture groups, named groups, and zero-based start/end offsets in Unicode code points. End offsets are exclusive. Matches follow Python's non-overlapping `finditer` behavior, including zero-length matches. The full input is held in memory, and Python regex execution has no timeout.
