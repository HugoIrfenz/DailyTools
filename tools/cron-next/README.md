# Cron Next

Validate a standard five-field cron expression and preview its next run times. Cron Next handles IANA timezones, daylight-saving transitions, lists, ranges, steps, and English month or weekday names using only Python's standard library.

## Prerequisites

Python 3.9 or newer with timezone data available to `zoneinfo`. Linux and macOS usually provide this through the operating system; some minimal containers and Windows installations may need the separate system/runtime timezone database. `UTC` always works. The tool makes no network requests and changes no files.

Run the commands below from the repository root. Use `python3` if that is your Python command.

## Usage

Quote the expression so the shell does not expand `*`:

```bash
python tools/cron-next/cron_next.py "*/15 9-17 * * MON-FRI"
python tools/cron-next/cron_next.py "0 2 1 * *" --timezone Asia/Jakarta --count 10
python tools/cron-next/cron_next.py "0 0 29 FEB *" --from 2027-01-01 --json
```

| Option | Behavior |
| --- | --- |
| `--timezone ZONE` | Evaluate in an installed IANA timezone such as `Asia/Jakarta` (default `UTC`). |
| `--from ISO_TIME` | Search strictly after an ISO 8601 date/datetime. A naive value uses `--timezone`; an offset-aware value is converted to it. Default: now. |
| `--count N` | Return 1–100 occurrences (default 5). |
| `--max-years N` | Search 1–20 years ahead (default 5). |
| `--json` | Emit a compact machine-readable report. |

Exit status is `0` when all requested occurrences are found, `1` when the search horizon ends first, and `2` for an invalid expression, option, timestamp, or timezone.

## Runnable example

This fixed start time makes the output reproducible:

```bash
python tools/cron-next/cron_next.py "*/15 9-17 * * MON-FRI" \
  --from 2026-10-09T16:50:00 --timezone Asia/Jakarta --count 3
```

```text
Expression: */15 9-17 * * MON-FRI
Timezone: Asia/Jakarta
Next 3 occurrence(s):
1. 2026-10-09T17:00+07:00
2. 2026-10-09T17:15+07:00
3. 2026-10-09T17:30+07:00
```

For CI or another program:

```bash
python tools/cron-next/cron_next.py "0 9 * * MON" \
  --from 2026-10-09 --timezone Asia/Jakarta --count 2 --json
```

```json
{"ok":true,"expression":"0 9 * * MON","timezone":"Asia/Jakarta","from":"2026-10-09T00:00+07:00","occurrences":["2026-10-12T09:00+07:00","2026-10-19T09:00+07:00"],"requested_count":2,"max_years":5}
```

## Supported syntax

The five fields are `minute hour day-of-month month day-of-week`:

| Form | Example | Meaning |
| --- | --- | --- |
| Wildcard | `*` | Every allowed value |
| List | `0,15,30,45` | Any listed value |
| Range | `9-17` | Inclusive range |
| Step | `*/10`, `9-17/2` | Every Nth value in a wildcard or range |
| Names | `JAN-MAR`, `MON-FRI` | Case-insensitive English abbreviations |

Ranges must ascend and do not wrap. Sunday may be `0`, `7`, or `SUN`. When both day-of-month and day-of-week are restricted, a time matches if **either** field matches, following traditional cron behavior. When only one is restricted, that field must match.

## Limitations

- This is deliberately the portable five-field format. Seconds, years, nicknames such as `@daily`, Quartz tokens (`?`, `L`, `W`, `#`), hashed/random values, environment assignments, and command text are not supported.
- Matching starts strictly after `--from` and has one-minute precision. Seconds and microseconds in the supplied start time are ignored only after advancing to the next minute.
- The tool predicts calendar matches; it does not inspect a cron daemon, confirm that a job is installed, or account for downtime, retry policies, scheduler jitter, or implementation-specific behavior.
- Search proceeds through real UTC minutes and converts each to the requested timezone. A nonexistent local time in a daylight-saving spring gap is skipped. A repeated local time during a fall-back can appear twice with different UTC offsets.
- A naive timestamp inside an ambiguous daylight-saving fold uses Python's first occurrence. Supply an explicit UTC offset to disambiguate the starting instant.
- Timezone rules come from the installed timezone database and may differ if that database is old. JSON output records the requested timezone name and includes numeric offsets on every occurrence.
- Sparse or impossible schedules may scan to `--max-years`; a partial result is considered unsuccessful and exits with status 1.

## Checks

```bash
python -m unittest discover -s tools/cron-next -v
```

Tests cover lists, ranges, steps and names; invalid syntax and bounds; strict-after behavior; day-of-month/day-of-week rules; leap days; all Sunday spellings; Asia/Jakarta offsets; daylight-saving gaps and repeated times in America/New_York; impossible schedules and search horizons; text/JSON CLI output; and exit statuses.
