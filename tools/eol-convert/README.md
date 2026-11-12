# EOL Convert

Convert LF, CRLF, and lone CR endings to one selected format. Requires Python 3.9+ and uses the standard library.

```bash
printf 'one\r\ntwo\rthree\n' | python tools/eol-convert/eol_convert.py --to lf
python tools/eol-convert/eol_convert.py input.txt --to crlf > converted.txt
```

Reads bytes in chunks and writes to stdout. Preserves other bytes and leaves an unterminated last line unterminated. Intended for UTF-8 and other ASCII-compatible text encodings. Use a separate destination file when redirecting output.
