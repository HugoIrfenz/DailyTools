# Duration Sum

Add durations and print a normalized total, using integer microseconds. Requires Python 3.9+, no third-party dependencies.

From the repository root:

```bash
python tools/duration-sum/duration_sum.py '1h30m' '45m'
# 2h 15m
python tools/duration-sum/duration_sum.py --json -- '1h' '-90m'
# {"microseconds": -1800000000, "normalized": "-30m"}
python -m unittest discover -s tools/duration-sum -v
```

Units are lowercase `d`, `h`, `m`, `s`, `ms`, and `us`. Terms can be adjacent or whitespace-separated. An optional leading sign applies to the entire argument; use `--` before arguments starting with `-`. Repeated units and decimal numbers such as `0.5h` are accepted. Each term must resolve to whole microseconds; finer values are rejected, not rounded. Each argument is limited to 4096 characters.

A day means 24 hours. This does not parse clock times, calendar dates, ISO durations, months, or years. JSON totals may exceed the exact integer range of JavaScript numbers. Exit code: 0 on success, 2 for invalid input.
