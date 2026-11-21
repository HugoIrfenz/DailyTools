# Number Stats

Summarize finite decimal numbers supplied one per line. Requires Python 3.9+ with no third-party packages.

```bash
printf '0.1\n0.2\n' | python tools/number-stats/number_stats.py -
python tools/number-stats/number_stats.py measurements.txt
```

JSON output includes count, min, max, sum, and mean. Numeric results are decimal strings. The example has sum `0.3` and mean `0.15`. Blank lines are ignored. Values are held in memory, with at most 10,000 digits and adjusted exponent magnitude 10,000 per value. Sum uses sufficient decimal precision for the inputs. Repeating means are rounded using decimal half-even rounding with at least 28 significant digits.
