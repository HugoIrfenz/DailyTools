# Unicode Normalize

Normalize UTF-8 text using Unicode NFC, NFD, NFKC, or NFKD. Input can come from a file or standard input; normalized UTF-8 is written to standard output.

Requires Python 3.9 or newer. It uses only the standard library.

```bash
python tools/unicode-normalize/unicode_normalize.py input.txt --form NFC > normalized.txt
printf 'Cafe\u0301\n' | python tools/unicode-normalize/unicode_normalize.py -
```

Use `--check` to write no text and test whether normalization would change the input. Exit status is 0 when already normalized, 1 when a change is required, and 2 for input or argument errors.

```bash
python tools/unicode-normalize/unicode_normalize.py input.txt --form NFC --check
```

The tool reads the complete input into memory and accepts UTF-8 only. NFKC and NFKD apply compatibility mappings, so they can change characters more substantially than NFC or NFD. The Unicode data version comes from the Python runtime. Output is not written in place.
