# Decimal Round

Round decimal arguments to a fixed number of fractional places. Requires Python 3.9+ with no third-party packages.

```bash
python tools/decimal-round/decimal_round.py 2.345 2.355 --places 2
python tools/decimal-round/decimal_round.py --mode half-up --places 2 -- -2.345
```

These print `2.34`, `2.36`, and `-2.35`. Default rounding is half-even. The half-up mode rounds ties away from zero. Places accepts 0 through 1000. Inputs must be finite, with at most 1000 digits and adjusted exponent magnitude 1000. All arguments are validated before printing results.
