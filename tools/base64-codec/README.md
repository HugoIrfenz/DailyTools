# Base64 Codec

Encode a file or stdin as Base64, or decode Base64 to raw bytes. Requires Python 3.9+, standard library only.

Run from the repository root:

```bash
printf 'hello' | python tools/base64-codec/base64_codec.py encode
# aGVsbG8=
printf 'aGVsbG8=' | python tools/base64-codec/base64_codec.py decode
# hello (no newline added)
python tools/base64-codec/base64_codec.py encode image.bin --urlsafe
python -m unittest discover -s tools/base64-codec -v
```

The optional file argument defaults to `-` (stdin). `--urlsafe` selects `-` and `_` instead of `+` and `/` for both operations. Encoded output ends in one newline. Decoded output is binary: redirect it to a new file when appropriate; shell redirection can overwrite files.

Decoding ignores ASCII space, tab, CR, and LF. It requires canonical encoding with padding where needed; missing/extra padding, nonzero unused bits, other whitespace, and the wrong alphabet are rejected before output. Unpadded URL tokens are not supported. Input is limited to 16 MiB including whitespace and is held in memory. Base64 is encoding, not encryption. Exit codes: 0 success, 2 invalid input or I/O error.
