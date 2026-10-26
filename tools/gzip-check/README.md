# Gzip Check

Fully decompress gzip data to validate its header, compressed stream, CRC, and trailer. It reports compressed and uncompressed byte counts, their size ratio, and the SHA-256 digest of the uncompressed bytes.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/gzip-check/gzip_check.py archive.gz
cat archive.gz | python tools/gzip-check/gzip_check.py - --json
python tools/gzip-check/gzip_check.py archive.gz --expect-sha256 HEX_DIGEST
```

Invalid, truncated, or CRC-mismatched input exits with status 1. Concatenated gzip members are decompressed as one byte stream. The entire compressed and uncompressed content is held in memory; this command does not list individual members or write the decompressed data.

Run the tests:

```bash
python -m unittest discover -s tools/gzip-check -p 'test_*.py'
```
