# Query Decode

Decode an UTF-8 form query string to ordered JSON name/value pairs. Repeated names and empty values are retained. Python 3.10+; standard library only, no network requests.

From the repository root:

```bash
printf 'tag=go&tag=python&q=hello+world' | python tools/query-decode/query_decode.py -
python tools/query-decode/query_decode.py query.txt --max-fields 1000
```

The first command returns pairs for `tag=go`, `tag=python`, and `q=hello world`. Input files are unchanged. Exit `0` means decoded; `2` means invalid input, read failure, or argument error.

Limits: input is a query, not a full URL. One leading `?` and one terminal LF/CRLF are accepted. `&` separates fields; `+` means space. Invalid percent escapes and invalid UTF-8 are rejected. Empty segments are ignored by Python's parser; fields without `=` have empty values. Input is held in memory. Output includes all supplied names and values, so do not share it when the query contains secrets.

Tests: `python -m unittest discover -s tools/query-decode -v` checks duplicates, Unicode, escaping, empty values, limits, and file/stdin CLI errors.
