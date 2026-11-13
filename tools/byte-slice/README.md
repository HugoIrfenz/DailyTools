# Byte Slice

Copy up to a given number of bytes from a zero-based offset to binary stdout. Requires Python 3.9+ with no third-party packages.

```bash
printf 'abcdef' > sample.bin
python tools/byte-slice/byte_slice.py sample.bin 2 3 > slice.bin
```

The example writes `cde`. Input must be seekable. A range beyond EOF returns only available bytes, and offsets at or beyond EOF produce empty output. Use a different output filename from the input.
