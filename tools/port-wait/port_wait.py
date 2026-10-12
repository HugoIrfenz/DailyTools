#!/usr/bin/env python3
"""Wait until a TCP host and port accept connections."""

import argparse
import json
import math
import socket
import sys
import time


def host_value(value):
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    if (not value or len(value) > 253 or value != value.strip() or
            any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise argparse.ArgumentTypeError("host must be a non-empty name or address")
    return value


def port_value(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return number


def duration_value(value, allow_zero=False):
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("duration must be a number") from exc
    minimum_ok = number >= 0 if allow_zero else number > 0
    if not math.isfinite(number) or not minimum_ok:
        relation = "non-negative" if allow_zero else "greater than zero"
        raise argparse.ArgumentTypeError(f"duration must be finite and {relation}")
    return number


def stable_value(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("stable count must be an integer") from exc
    if not 1 <= number <= 100:
        raise argparse.ArgumentTypeError("stable count must be between 1 and 100")
    return number


def tcp_connect(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_for_port(host, port, timeout=30.0, interval=0.25,
                  connect_timeout=1.0, stable=1, connector=tcp_connect,
                  clock=time.monotonic, sleeper=time.sleep):
    """Probe until stable consecutive successes or the total timeout expires."""
    started = clock()
    deadline = started + timeout
    attempts = 0
    streak = 0
    while True:
        attempts += 1
        remaining = max(0.0, deadline - clock())
        attempt_timeout = max(0.001, min(connect_timeout, remaining or 0.001))
        if connector(host, port, attempt_timeout):
            streak += 1
            if streak >= stable:
                elapsed = max(0.0, clock() - started)
                return {
                    "ok": True, "host": host, "port": port,
                    "attempts": attempts, "stable_required": stable,
                    "consecutive_successes": streak,
                    "elapsed_seconds": round(elapsed, 3),
                }
        else:
            streak = 0
        now = clock()
        if now >= deadline:
            return {
                "ok": False, "host": host, "port": port,
                "attempts": attempts, "stable_required": stable,
                "consecutive_successes": streak,
                "elapsed_seconds": round(max(0.0, now - started), 3),
            }
        sleeper(min(interval, deadline - now))


def endpoint(host, port):
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def text_report(report, timeout):
    target = endpoint(report["host"], report["port"])
    if report["ok"]:
        return (f"READY: {target} accepted {report['stable_required']} consecutive "
                f"connection(s) after {report['attempts']} attempt(s) in "
                f"{report['elapsed_seconds']:.3f}s.")
    return (f"TIMEOUT: {target} did not accept {report['stable_required']} consecutive "
            f"connection(s) within {timeout:.3f}s after {report['attempts']} attempt(s).")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", type=host_value, help="DNS name, IPv4, or IPv6 address")
    parser.add_argument("port", type=port_value, help="TCP port, 1-65535")
    parser.add_argument("--timeout", type=lambda value: duration_value(value, True),
                        default=30.0, metavar="SECONDS",
                        help="total wait time; zero performs one probe (default: 30)")
    parser.add_argument("--interval", type=duration_value, default=0.25,
                        metavar="SECONDS", help="delay between probes (default: 0.25)")
    parser.add_argument("--connect-timeout", type=duration_value, default=1.0,
                        metavar="SECONDS", help="per-probe upper bound (default: 1)")
    parser.add_argument("--stable", type=stable_value, default=1, metavar="N",
                        help="required consecutive successes, 1-100 (default: 1)")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)
    try:
        report = wait_for_port(args.host, args.port, args.timeout, args.interval,
                               args.connect_timeout, args.stable)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    print(json.dumps(report, ensure_ascii=True, separators=(",", ":"))
          if args.json else text_report(report, args.timeout))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
