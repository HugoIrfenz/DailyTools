# Delimited Convert

Convert UTF-8 records between `comma`, `tab`, `semicolon`, and `pipe` delimiters. Requires Python 3.9+ with no third-party packages.

```bash
printf 'name;city\n"Ana;Budi";Jakarta\n' | python tools/delimited-convert/delimited_convert.py - --from semicolon --to comma
python tools/delimited-convert/delimited_convert.py report.tsv --from tab --to comma > report.csv
```

The example produces `Ana;Budi,Jakarta` as the data row. Uses double-quote CSV escaping and CRLF output. Rows can have different widths. Output can contain earlier rows if a later record fails to parse.
