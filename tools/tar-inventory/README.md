# TAR Inventory

Summarize TAR archive metadata without extracting entries. It counts regular files, directories, links and other entry types; reports logical file bytes, duplicate names, suspicious paths or link targets, and the largest regular files. Uncompressed TAR and formats recognized by Python's `tarfile` module, including gzip, bzip2, and xz, are accepted.

Requires Python 3.9 or newer and has no dependencies.

```bash
python tools/tar-inventory/tar_inventory.py backup.tar.gz --top 10
python tools/tar-inventory/tar_inventory.py backup.tar --json
```

The tool reads archive headers and does not extract members or read regular-file payloads. Logical size is the sum recorded in file headers, not disk usage. Suspicious-path detection is advisory and checks absolute paths, `..` components, and link targets; it is not a complete archive security scan. Member metadata is loaded into memory.
