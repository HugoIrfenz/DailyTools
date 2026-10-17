# File Compare

Compare two regular files byte by byte and report the first differing offset (zero-based). A shorter file differs at its end when it is a prefix of the other. File contents are not printed.

Requires Python 3.9+, standard library only. Run from the repository root:

```bash
python tools/file-compare/file_compare.py README.md README.md
python tools/file-compare/file_compare.py before.bin after.bin --json
python -m unittest discover -s tools/file-compare -v
```

The first command reports `Equal` and the byte count. JSON contains `equal`, `first_difference` (null when equal), `left_bytes`, and `right_bytes`. Exit codes: 0 equal, 1 different, 2 argument or read error.

Reads chunks of up to 1 MiB and stops at the first difference. Sizes are measured before comparison. Inputs must remain unchanged during the run; this is not a filesystem snapshot. Symlinks to regular files are followed. Directories and special files are rejected; concurrent path replacement is not guarded against. No file is modified.
