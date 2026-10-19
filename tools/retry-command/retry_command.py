#!/usr/bin/env python3
"""Retry a local command on nonzero exit or per-attempt timeout, without a shell."""

import argparse
import math
import subprocess
import sys
import time


def attempts_value(value):
    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("attempts must be an integer") from exc
    if not 1 <= count <= 100:
        raise argparse.ArgumentTypeError("attempts must be between 1 and 100")
    return count


def seconds_value(value):
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("seconds must be a number") from exc
    if not math.isfinite(seconds) or not 0 <= seconds <= 3600:
        raise argparse.ArgumentTypeError("seconds must be finite and between 0 and 3600")
    return seconds


def retry(command, attempts=3, delay=1.0, timeout=None):
    if not command:
        raise ValueError("command is required")
    if not 1 <= attempts <= 100:
        raise ValueError("attempts must be between 1 and 100")
    if not math.isfinite(delay) or not 0 <= delay <= 3600:
        raise ValueError("delay must be finite and between 0 and 3600")
    if timeout is not None and (not math.isfinite(timeout) or not 0 < timeout <= 3600):
        raise ValueError("timeout must be finite, positive and at most 3600 seconds")
    for attempt in range(1, attempts + 1):
        try:
            completed = subprocess.run(command, timeout=timeout, shell=False)
        except subprocess.TimeoutExpired:
            reason = "timed out"
        else:
            if completed.returncode == 0:
                return 0
            reason = f"exited with {completed.returncode}"
        print(f"retry-command: attempt {attempt}/{attempts} {reason}",
              file=sys.stderr, flush=True)
        if attempt < attempts:
            time.sleep(delay)
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempts", type=attempts_value, default=3,
                        help="total attempts, including the first (1..100; default 3)")
    parser.add_argument("--delay", type=seconds_value, default=1.0,
                        help="seconds between failed attempts (0..3600; default 1)")
    parser.add_argument("--timeout", type=seconds_value,
                        help="positive per-attempt timeout, at most 3600 seconds")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="command and arguments, normally after --")
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("command is required after --")
    try:
        return retry(command, args.attempts, args.delay, args.timeout)
    except (OSError, ValueError) as exc:
        print(f"retry-command: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
