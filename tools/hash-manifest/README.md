# Hash Manifest

Create a deterministic SHA-256 inventory for a directory, then verify that its regular files have not changed or disappeared. An optional strict check also reports new files that are absent from the manifest. Symlinks are never followed.

## Prerequisites

Python 3.9 or newer. No packages to install and no network access is used. Creating a manifest writes only the specified manifest path; verification is read-only. Run the commands below from the repository root, using `python3` if that is your Python command.

## Usage

```bash
python tools/hash-manifest/hash_manifest.py create ./release ./release-manifest.json
python tools/hash-manifest/hash_manifest.py verify ./release ./release-manifest.json
python tools/hash-manifest/hash_manifest.py verify ./release ./release-manifest.json --check-extra --json
```

### Create options

| Option | Behavior |
| --- | --- |
| `--force` | Atomically replace an existing manifest. Without it, overwriting is refused. |
| `--json` | Emit a compact machine-readable operation report. |

### Verify options

| Option | Behavior |
| --- | --- |
| `--check-extra` | Also report regular files under the root that are not listed. |
| `--max-issues N` | Keep at most N issue details (default 20), while retaining the full count. Zero keeps counts only. |
| `--json` | Emit a compact machine-readable verification report. |

Creation exits `0` on success and `2` for an input, scan, or write error. Verification exits `0` when everything requested matches, `1` for missing, modified, wrong-type, unreadable, or extra files, and `2` for an invalid/unreadable manifest, bad root, or bad arguments.

## Runnable example

Create a manifest for the included [sample directory](examples/sample):

```bash
python tools/hash-manifest/hash_manifest.py create \
  tools/hash-manifest/examples/sample sample-manifest.json
```

```text
CREATED: 2 file(s), 23 byte(s); skipped 0 symlink(s) and 0 special file(s).
```

Verify it, including a check for unlisted regular files:

```bash
python tools/hash-manifest/hash_manifest.py verify \
  tools/hash-manifest/examples/sample sample-manifest.json --check-extra
```

```text
OK: 2/2 expected file(s) matched; 0 issue(s).
```

The manifest is UTF-8 JSON with stable path ordering:

```json
{
  "algorithm": "sha256",
  "files": [
    {"path": "config.json", "sha256": "...64 lowercase hex characters...", "size": 17},
    {"path": "hello.txt", "sha256": "...64 lowercase hex characters...", "size": 6}
  ],
  "format": "dailytools-hash-manifest-v1"
}
```

Delete `sample-manifest.json` when finished. If the manifest itself is placed inside the scanned root, the tool excludes that exact file automatically from creation and `--check-extra`.

## What is checked

- Paths are stored relative to the selected root in canonical POSIX form and sorted for deterministic output.
- Each regular file records its byte size and a streaming SHA-256 digest. Files are rechecked after reading so a size, modification-time, or file-identity change during hashing fails the operation.
- Verification rejects absolute paths, parent traversal, duplicates, malformed digests, unsafe separators, and control characters before accessing listed paths.
- Every parent directory of a listed file is inspected during verification. A symlink or non-directory in that chain is a `type_mismatch`, not a path to follow.
- The manifest is written through a temporary sibling file and atomically moved into place. Existing manifests require explicit `--force`.

## Limitations

- SHA-256 detects content differences but does not authenticate who created the manifest. An attacker able to replace both files and manifest can produce matching hashes; store, sign, or transmit the manifest separately when authenticity matters.
- File contents are never printed. The manifest and reports do reveal relative filenames, byte sizes, digests, and issue locations; treat filenames as metadata that may be sensitive.
- Symlinks (including symlinked directories), sockets, devices, and other special files are skipped. Hard-linked regular files are listed once per path. Permissions, ownership, timestamps, extended attributes, and empty directories are not recorded.
- For portable and terminal-safe manifests, relative paths containing backslashes, colons, ASCII control characters, or non-canonical components are rejected. Unicode and spaces are supported.
- Creation and verification are not filesystem snapshots. The tool detects changes while each file is open, but another process may change an already-hashed file later in the same run.
- `--check-extra` reports only additional regular files. It deliberately ignores skipped symlinks and special files while returning their counts in JSON output.
- Hashing reads every listed byte and can be I/O intensive for large trees. Memory use is bounded by the manifest, file list, issue details, and a 1 MiB read buffer rather than total file content.

## Checks

```bash
python -m unittest discover -s tools/hash-manifest -v
```

Tests cover deterministic sorted output, binary and nested files, manifests inside the root, clean verification, modified/missing/extra files, empty directories, symlink skipping and replacement attacks, overwrite protection, malicious and duplicate paths, invalid schema/size/digests, issue-detail caps across 50 failures, JSON CLI output, and exit statuses.
