# JWT Inspect

Decode the JSON header and payload from a three-segment compact token. Output also reports whether a signature segment is present and its decoded byte length. Requires Python 3.9+, standard library only.

From the repository root:

```bash
printf '%s' 'eyJhbGciOiJub25lIn0.eyJzdWIiOiIxMjMifQ.' | python tools/jwt-inspect/jwt_inspect.py --pretty
python tools/jwt-inspect/jwt_inspect.py token.txt
python -m unittest discover -s tools/jwt-inspect -v
```

Input defaults to stdin (`-`) and is limited to 64 KiB. ASCII space, tab, CR, and LF around the token are ignored. Segments must use canonical unpadded base64url. Header and payload must be UTF-8 JSON objects; duplicate keys and non-finite numbers are rejected. The signature may be empty. Output is JSON and therefore includes decoded claim values; handle it according to the token's sensitivity. Input files are not modified.

This tool does not verify signatures, algorithms, keys, issuers, audiences, timestamps, claim meanings, or whether a token should be trusted. It does not decrypt encrypted tokens and only accepts three segments. Successful decoding means the structure was readable, not that the token is authentic or valid. Exit codes: 0 decoded, 2 argument, format, or I/O error.
