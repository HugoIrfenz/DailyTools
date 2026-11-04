# URL Inspect

Reads one URL per line and reports its scheme, authority presence, host, IDNA host form, port, path, segment count, query parameter count, fragment presence, and credential presence. It does not print usernames, passwords, query values, or fragment values.

Requires Python 3.9 or newer. It has no third-party dependencies and makes no network requests.

```bash
python tools/url-inspect/url_inspect.py urls.txt
printf 'https://example.com:8443/docs?a=1\n' | python tools/url-inspect/url_inspect.py -
```

Blank lines are ignored. Relative references are accepted. Whitespace, control characters, invalid ports, malformed IPv6 authorities, invalid UTF-8, and hosts that cannot be encoded with IDNA are rejected. This parses URL structure but does not test reachability or determine whether a URL is trustworthy.

```bash
python -m unittest discover -s tools/url-inspect -p 'test_*.py'
```
