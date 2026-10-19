# Retry Command

Run a local command again after a nonzero exit or per-attempt timeout. Requires Python 3.9+, standard library only.

From the repository root:

```bash
python tools/retry-command/retry_command.py --attempts 3 --delay 1 --timeout 10 -- python -c "print('ready')"
python -m unittest discover -s tools/retry-command -v
```

The example prints `ready` once. `--attempts` includes the initial run (1–100, default 3). `--delay` is seconds between failures (0–3600, default 1). `--timeout` is per attempt, must be positive and at most 3600 seconds; it is omitted by default. Options for the wrapper go before `--`; the executable and its arguments go after it. No shell is used, so pipes, wildcards and redirection are not interpreted by the wrapper.

Child stdout/stderr pass through; failure summaries go to stderr. Exit codes: 0 if an attempt succeeds, 1 if attempts are exhausted, 2 for invalid options or launch errors, 130 when interrupted. The child's final exit code appears in the failure summary, not as the wrapper's exit code. Launch errors are not retried.

Only rerun commands whose repeated side effects are acceptable. A timeout terminates and waits for the direct child, not its process tree; descendants may remain. Process creation time is not covered by the timeout. There is no total wall-clock deadline or backoff. The child inherits the working directory, environment and stdin. Avoid interactive commands that consume input across attempts.
