# ZIP Inventory

Read ZIP directory metadata to report entry counts, compressed/uncompressed byte totals, encryption flags, exact duplicate names, and the largest files. No extraction is performed.

Requires Python 3.9+, standard library only. From the repository root:

```bash
python tools/zip-inventory/zip_inventory.py archive.zip
python tools/zip-inventory/zip_inventory.py archive.zip --top 5 --json
python -m unittest discover -s tools/zip-inventory -v
```

Reproducible example (creates or overwrites `sample.zip` in the current directory):

```bash
python -c "import zipfile; z=zipfile.ZipFile('sample.zip','w'); z.writestr('hello.txt','hello'); z.close()"
python tools/zip-inventory/zip_inventory.py sample.zip --json
```

The example contains one file with 5 uncompressed and 5 compressed bytes. Totals sum all directory records, including duplicate entries; compressed totals exclude ZIP headers and directory overhead, so they are not archive file size. `--top` accepts 0–1000 (default 10). Largest files sort by descending uncompressed bytes, then name, then zero-based directory `entry_index`. Directories are entries whose names end in `/`; other entries count as files. Displayed names are JSON-escaped.

Sizes and encryption status are metadata claims, not verified payload properties. Member contents, CRCs, passwords, and extraction paths are not checked. The ZIP directory is loaded into memory even with `--top 0`; very large or malformed directories may consume substantial resources. Keep the archive unchanged while reading. Exit codes: 0 on success, 2 for argument, format, or I/O errors.
