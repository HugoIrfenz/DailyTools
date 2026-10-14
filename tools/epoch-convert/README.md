# Epoch Convert

Convert Unix seconds/milliseconds and offset-aware ISO datetimes. Returns UTC plus decimal seconds and milliseconds as strings, using integer microseconds rather than float rounding. Requires Python 3.9+; standard library only, no network or file writes.

From the repository root:

```bash
python tools/epoch-convert/epoch_convert.py from-epoch 1700000000123 --unit milliseconds --json
python tools/epoch-convert/epoch_convert.py to-epoch 1970-01-01T07:00:00+07:00
```

The second command reports UTC `1970-01-01T00:00:00.000000+00:00`, seconds `0`, and milliseconds `0`. Exit `0` means converted; `2` means invalid input or arguments.

Limits: timestamps use plain decimal notation (up to six fractional digits for seconds, three for milliseconds). ISO input requires `YYYY-MM-DDTHH:MM:SS[.fraction]` with `Z` or an explicit `±HH:MM` offset. Naive datetimes, named timezones, leap seconds, scientific notation, and precision beyond microseconds are unsupported. Dates must remain within Python's years 1–9999.

Tests: `python -m unittest discover -s tools/epoch-convert -v` checks negative timestamps, microsecond roundtrips, offsets, leap dates, range/precision errors, and CLI output.
