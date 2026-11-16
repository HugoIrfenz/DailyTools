# Date Range

Print one ISO calendar date per line, including both endpoints. Requires Python 3.9+ with no third-party packages.

```bash
python tools/date-range/date_range.py 2026-11-13 2026-11-16 --weekdays
```

This prints `2026-11-13` and `2026-11-16`. The optional filter includes Monday through Friday. It does not use holiday calendars or time zones.
