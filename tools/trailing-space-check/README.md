# Trailing Space Check

Report lines ending in ASCII spaces or tabs in UTF-8 files. Requires Python 3.9+ with no third-party packages.

```bash
printf 'clean\nextra \t\n' | python tools/trailing-space-check/trailing_space_check.py -
python tools/trailing-space-check/trailing_space_check.py notes.txt other.txt
```

The first command prints `{"file": "-", "line": 2, "count": 2}`. Exit status is 0 for clean input, 1 for findings, and 2 for errors. The checker also flags intentional trailing spaces, such as Markdown hard breaks. It reads without modifying files.
