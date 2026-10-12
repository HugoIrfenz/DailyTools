# Port Wait

Wait until a TCP endpoint is ready before starting the next command in a deployment, container entrypoint, local development script, or CI job. Port Wait retries quietly, supports a total timeout and consecutive-success requirement, and can emit JSON for automation.

## Prerequisites

Python 3.9 or newer. No packages to install. The tool performs outbound TCP connection attempts only to the host and port you provide; it sends no application data and changes no files.

Run commands from the repository root. Use `python3` if that is your Python command.

## Usage

```bash
python tools/port-wait/port_wait.py localhost 5432
python tools/port-wait/port_wait.py database 5432 --timeout 60 --interval 0.5
python tools/port-wait/port_wait.py redis 6379 --stable 3 --json
```

IPv6 literals may be written with or without brackets:

```bash
python tools/port-wait/port_wait.py ::1 8080
python tools/port-wait/port_wait.py '[::1]' 8080
```

| Option | Behavior |
| --- | --- |
| `--timeout SECONDS` | Total wait budget (default 30). Zero performs exactly one probe. |
| `--interval SECONDS` | Positive delay between probes (default 0.25). |
| `--connect-timeout SECONDS` | Positive per-probe connection bound (default 1), reduced to the remaining total budget when smaller. |
| `--stable N` | Require 1–100 consecutive successful connections (default 1). A failure resets the streak. |
| `--json` | Emit a compact machine-readable result. |

Exit status is `0` when the required streak succeeds, `1` when the total timeout expires, `2` for invalid arguments, and `130` when interrupted with Ctrl+C.

## Runnable local example

Start a temporary HTTP server in one terminal:

```bash
python -m http.server 8765 --bind 127.0.0.1
```

Then probe it from another terminal:

```bash
python tools/port-wait/port_wait.py 127.0.0.1 8765 --timeout 5 --stable 2
```

A typical result is:

```text
READY: 127.0.0.1:8765 accepted 2 consecutive connection(s) after 2 attempt(s) in 0.250s.
```

The exact elapsed time and attempt count depend on when the server becomes reachable. JSON mode has stable field names:

```json
{"ok":true,"host":"127.0.0.1","port":8765,"attempts":2,"stable_required":2,"consecutive_successes":2,"elapsed_seconds":0.25}
```

In a POSIX shell deployment script, a successful check allows the next command to run:

```bash
python tools/port-wait/port_wait.py database 5432 --timeout 60 --stable 2 \
  && python app.py
```

## Behavior and limitations

- A success means a TCP connection was accepted and immediately closed. It does not prove that an HTTP route, database login, TLS handshake, migration, or application-level health check will succeed.
- Hostnames are resolved by the operating system on every attempt. DNS failures are treated as failed probes and retried until the deadline; DNS resolution itself may not honor the socket connect timeout on every platform.
- `socket.create_connection` can try multiple resolved addresses. On some platforms each address may consume much of the per-probe timeout, so the total duration is a practical bound rather than a hard real-time guarantee.
- `--stable` creates and closes one connection per successful probe, separated by `--interval`. Choose a modest count to avoid unnecessary connection churn or noisy server logs.
- No protocol bytes are sent. Services that require a client message before considering a session healthy need a protocol-specific health checker instead.
- Connection errors are intentionally summarized as retries rather than exposed individually. This keeps output stable but does not distinguish refused connections, routing failures, DNS errors, or firewall timeouts.
- Floating-point durations are accepted, but must be finite. Scheduling and elapsed-time measurement use a monotonic clock; operating-system load can make sleeps and reported completion slightly later than requested.
- Only TCP is supported. UDP sockets, Unix-domain sockets, HTTP status checks, TLS certificate validation, and command execution are outside this tool's scope.

## Checks

```bash
python -m unittest discover -s tools/port-wait -v
```

Tests cover immediate and delayed success, retry intervals, total-timeout clamping, zero-timeout single probes, consecutive-success streaks and resets, per-probe timeout reduction, IPv4/name/IPv6 formatting, duration/host/port validation, real loopback listener connections, closed-port timeout behavior, JSON output, and exit statuses.
