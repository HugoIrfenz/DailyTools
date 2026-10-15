# Path Collisions

Find relative paths that have the same Unicode NFC + casefold comparison key. For example, `Config.json` and `config.json` are reported together. Requires Python 3.9+; standard library only.

From the repository root:

```bash
python tools/path-collisions/path_collisions.py ./project --json
python tools/path-collisions/path_collisions.py ./project --case-sensitive --max-groups 5
```

The scan includes files, directories, hidden entries, and symlink names. Symlinked directories are not traversed. `--case-sensitive` compares NFC-normalized paths without casefold. `--max-groups` limits displayed groups (default 20); counts still cover the full scan. Text output quotes/escapes paths.

Exit codes: `0` for no collisions under the selected rule, `1` for collisions, `2` for argument or scan errors. The tool reads directory entries without renaming or changing files; it makes no network requests.

Limits: this comparison rule is not an exact model of Windows, macOS, or a specific filesystem. It does not check reserved names, path lengths, permissions, or file contents. Full relative paths are compared, so conflicting parent directories and conflicting children can both appear as groups. Memory grows with entry count. Changes during a scan are not a snapshot. A symlink supplied directly as the root is rejected; symlinks in ancestor components are not separately checked.

Tests (run on Linux):

```bash
python -m unittest discover -s tools/path-collisions -v
```

Checks cover case/Unicode collisions, deterministic ordering, limits, nested/hidden entries, symlink handling, unchanged files, escaped output, and CLI errors. Case-collision fixtures require a case-sensitive filesystem.
