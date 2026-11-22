# Integer Base

Convert signed integers between bases 2 through 36. Requires Python 3.9+ with no third-party packages.

```bash
python tools/integer-base/integer_base.py ff --from 16 --to 2
python tools/integer-base/integer_base.py --from 10 --to 16 -- -255
```

These print `11111111` and `-ff`. Input accepts an optional sign and case-insensitive digits. Base prefixes, separators, and whitespace are rejected. Output uses lowercase digits. Python's configured integer-string length limit applies.
