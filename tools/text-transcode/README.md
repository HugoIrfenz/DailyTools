# Text Transcode

Convert text between explicit encodings, with strict decoding and encoding. Requires Python 3.9+, standard library only.

From the repository root:

```bash
printf 'hello' | python tools/text-transcode/text_transcode.py --from utf-8 --to utf-16-le
python tools/text-transcode/text_transcode.py source.txt --from latin-1 --to utf-8 > converted.txt
python -m unittest discover -s tools/text-transcode -v
```

The first example emits UTF-16 little-endian bytes without a BOM or added newline. The input file defaults to `-` (stdin); output is binary stdout. The source file is not modified by the tool, but shell redirection can overwrite files: use a different output path.

Encodings: `utf-8`, `utf-8-sig`, `utf-16-le`, `utf-16-be`, `latin-1`, and `ascii`. Input additionally accepts `utf-16`, which selects byte order from a BOM and rejects nonempty input without one. Explicit UTF-16 byte orders preserve an initial BOM as a text character. `utf-8-sig` removes an initial UTF-8 BOM on input and adds one on output, including empty output.

Input is limited to 16 MiB and held in memory. Newlines and NUL characters are preserved. There is no encoding detection or replacement of invalid characters; malformed input or unrepresentable output is rejected before writing converted bytes. Latin-1 accepts every byte, so selecting it incorrectly can produce unwanted text without an error. Exit codes: 0 success, 2 invalid input, options, or I/O error.
