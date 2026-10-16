# Tree Usage

Summarize regular-file counts and logical byte sizes by final extension. Requires Python 3.9+; standard library only. File contents are not read or modified, and no network requests are made.

From the repository root:

```bash
python tools/tree-usage/tree_usage.py ./project --json
python tools/tree-usage/tree_usage.py ./project --top 5
```

Groups are sorted by descending bytes, then extension. Extensions use casefold, so `.TXT` joins `.txt`. `archive.tar.gz` counts as `.gz`; `.env` and `README` have no extension. `--top` limits displayed groups (default 10), not totals. Exit `0` means scanned; `2` means an argument or scan error.

Limits: includes hidden entries; skips symlinks and special files, reporting their counts. Hard links count once per path. Sizes are logical `st_size` bytes, not allocated disk space; sparse files, compression, and shared blocks are not accounted for. Directory metadata is excluded. Memory grows with directory queue and extension groups. Concurrent changes are not a snapshot. A symlink root is rejected, but ancestor symlinks are not separately checked.

Tests (run on Linux):

```bash
python -m unittest discover -s tools/tree-usage -v
```

Checks include nested/hidden files, suffix grouping, limits, empty files, symlinks, hard links, FIFO skipping, unchanged contents, and CLI errors. FIFO fixtures require Unix.
