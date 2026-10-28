# Hex View

Display binary input as byte offsets, hexadecimal values, and printable ASCII. It reads a file or standard input and supports byte offsets, output length limits, and widths from 1 to 64 bytes.

Requires Python 3.9 or newer and has no dependencies.

```bash
python tools/hex-view/hex_view.py firmware.bin --offset 0x100 --length 64
printf 'hello' | python tools/hex-view/hex_view.py - --width 8
```

Offsets and lengths accept decimal values or Python-style prefixes such as `0x`. Bytes outside printable ASCII are shown as `.`; the tool does not decode text or modify input. An offset beyond the end of input produces no rows. Output is streamed, but skipping on non-seekable standard input requires reading and discarding preceding bytes.
