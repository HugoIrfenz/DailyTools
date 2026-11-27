# URL Defang

Convert HTTP(S) URLs into defanged plain-text forms for reports. Requires Python 3.9+ with no third-party packages.

```bash
printf 'https://example.com/a.js\n' | python tools/url-defang/url_defang.py -
python tools/url-defang/url_defang.py urls.txt
```

The example prints `hxxps://example[.]com/a[.]js`. Every literal dot after the scheme is replaced, including dots in paths and queries. Input contains one absolute HTTP(S) URL per line. Blank lines are ignored. All lines are checked before output. The tool uses memory proportional to input size. It does not assess destination reputation.
