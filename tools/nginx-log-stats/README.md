# Nginx Log Stats

Summarize Nginx or Apache Common/Combined access logs with request-method and status counts, 4xx/5xx totals, transferred bytes, and the most frequent request paths. Query strings are removed from path counts.

Requires Python 3.9 or newer and uses only the standard library.

```bash
python tools/nginx-log-stats/nginx_log_stats.py access.log
cat access.log | python tools/nginx-log-stats/nginx_log_stats.py --json --top 20
python tools/nginx-log-stats/nginx_log_stats.py access.log --no-paths
```

Lines outside the Common/Combined request format are counted as malformed. A `-` byte count contributes zero and is excluded from the known-byte line count. Paths may still contain identifiers; use `--no-paths` to omit them from the report. The input is processed locally.

Run tests with:

```bash
python -m unittest discover -s tools/nginx-log-stats -p 'test_*.py'
```
