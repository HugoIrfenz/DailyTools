# Duplicate Finder

Find byte-for-byte duplicate files recursively and estimate reclaimable disk space. The tool is deliberately **read-only**: it never deletes, moves, renames, or modifies files.

It first groups files by size, then hashes only groups that could contain duplicates. SHA-256 confirms exact matches.

## Requirements

- Python 3.9 or newer (`python3`, `python`, or `py -3`, depending on your system).
- Standard library only. No installation, account, or network access required.

Run commands from the repository root.

## Quick start

Scan a folder:

```bash
python tools/duplicate-finder/duplicate_finder.py /path/to/folder
```

Try the included safe example:

```bash
python tools/duplicate-finder/duplicate_finder.py tools/duplicate-finder/examples
```

Expected result:

```text
1 duplicate group(s); 34 B potentially reclaimable.
Hashed 2 size-matched file(s).

Group 1: 2 files × 34 B; reclaimable 34 B
  alpha.txt
  copy-of-alpha.txt
```

A duplicate result exits with status **1**. That means matches were found, not that the scan crashed.

## Useful options

Skip cache, dependency, and VCS directories:

```bash
python tools/duplicate-finder/duplicate_finder.py . \
  --exclude .git \
  --exclude node_modules \
  --exclude .venv \
  --exclude __pycache__
```

Ignore small files, for example anything below 1 MiB:

```bash
python tools/duplicate-finder/duplicate_finder.py ~/Downloads --min-size 1048576
```

Use relative-path or filename glob patterns:

```bash
python tools/duplicate-finder/duplicate_finder.py . \
  --exclude "build/*" \
  --exclude "*.tmp"
```

Produce a compact machine-readable report:

```bash
python tools/duplicate-finder/duplicate_finder.py ~/Downloads --json > duplicates.json
```

The JSON report includes duplicate groups, relative paths, SHA-256 digests, per-file sizes, estimated reclaimable bytes, number of hashed candidates, and scan errors.

## Safety behavior

- No deletion or modification capability exists.
- Symbolic links are skipped, including symlinked directories.
- Multiple hardlinks to the same physical file are counted once, so they are not presented as reclaimable copies.
- Files are checked again after hashing; a file that changes during the read becomes a scan error instead of a potentially false match.
- Paths in successful results are relative to the scanned root.
- Empty files are ignored by default. Pass `--min-size 0` to include them.

Always inspect reported paths yourself before removing anything with another program. Matching content does not tell you which copy is authoritative or whether applications depend on both paths.

## Exit codes

- **0:** scan completed with no duplicate groups.
- **1:** scan completed and duplicates were found.
- **2:** at least one scan/read error occurred, the root was invalid, or CLI arguments were invalid. A report is still produced when possible.

## Limitations

Every size-matched candidate must be read to calculate SHA-256, so large folders may take time and disk I/O. No filesystem ignore file is loaded automatically; exclusions are explicit. Permission errors and files changing during the scan cause exit code 2. Special files, symlinks, and repeated hardlinks are skipped. The reclaimable estimate assumes keeping one path in each group, but the tool does not decide which one.

## Verification

```bash
python -m unittest discover -s tools/duplicate-finder -v
```

The suite covers confirmed duplicates, same-size different content, reclaimable-byte calculations, minimum sizes and empty files, exclusion patterns, symlink and hardlink safety, invalid roots, JSON reports, clean and duplicate exit codes, invalid arguments, and human-readable sizes.
