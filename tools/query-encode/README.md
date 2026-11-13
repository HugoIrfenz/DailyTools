# Query Encode

Encode ordered `name=value` arguments as a UTF-8 form query string. Requires Python 3.9+ with no third-party packages.

```bash
python tools/query-encode/query_encode.py 'q=kopi susu' 'tag=go' 'tag=c++'
```

This prints `q=kopi+susu&tag=go&tag=c%2B%2B`. Repeated names and empty values are retained. The first equals sign splits the name from the value, and names must be nonempty. Inputs are treated as literal text, including any existing percent escapes. Use `--` before an argument starting with a dash.
