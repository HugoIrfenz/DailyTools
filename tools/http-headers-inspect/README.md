# HTTP Headers Inspect

Inventory names, duplicate counts, and value character totals from a raw HTTP request or response header block without printing header values. Processing is local and performs no network requests. Python 3.9+, standard library only.

```bash
python tools/http-headers-inspect/http_headers_inspect.py response-headers.txt
curl -sS -D - -o /dev/null https://example.com/ | python tools/http-headers-inspect/http_headers_inspect.py - --text
```

JSON is emitted by default. `--text` produces tab-separated summary rows. Field names are lowercased; repeated names are combined while retaining first-seen order. An optional first request/status line is counted but not printed.

Input must be UTF-8 and at most 1 MiB. CRLF and LF are accepted. Bare CR, NUL, invalid field names, control characters, obsolete folded fields, malformed lines, and content after the blank header terminator return exit 1. The parser inventories syntax and does not validate HTTP semantics, interpret values, or verify whether duplicated fields are permitted.

```bash
python -m unittest discover -s tools/http-headers-inspect -v
```
