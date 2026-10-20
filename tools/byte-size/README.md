# Byte Size

Parse a byte quantity into an exact integer and display decimal and binary sizes. Requires Python 3.9+, standard library only.

From the repository root:

```bash
python tools/byte-size/byte_size.py '1.5 GiB' --json
# {"bytes": 1610612736, "decimal": "1.61 GB", "binary": "1.50 GiB"}
python tools/byte-size/byte_size.py 1024
python -m unittest discover -s tools/byte-size -v
```

Decimal units are `B`, `kB` (also `KB`), `MB`, `GB`, `TB`, `PB`, `EB`, using powers of 1000. Binary units are `KiB` through `EiB`, using powers of 1024. Units are case-sensitive; a bare number means bytes. A decimal fraction is accepted only when it resolves to whole bytes. Signs, exponents, and bit units are not accepted; input is limited to 256 characters.

The byte count is exact. Human-readable values use two decimal places, rounded half up, and stop at EB/EiB; the selected unit is based on the unrounded count. Large JSON integers may lose precision in consumers using JavaScript numbers. Exit codes: 0 success, 2 invalid input.
