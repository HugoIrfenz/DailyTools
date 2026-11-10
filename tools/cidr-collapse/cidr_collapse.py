#!/usr/bin/env python3
"""Collapse overlapping and adjacent IPv4/IPv6 networks without adding addresses."""
import argparse
import ipaddress
import json
import sys
from pathlib import Path


def collapse(text, normalize=False):
    groups = {4: [], 6: []}
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            network = ipaddress.ip_network(line, strict=not normalize)
            if "%" in line:
                raise ValueError("zone identifiers are not supported")
        except ValueError as exc:
            raise ValueError("invalid network at line " + str(number)) from exc
        groups[network.version].append(network)
    return [str(network) for version in (4, 6)
            for network in ipaddress.collapse_addresses(groups[version])]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="one network per line, or - for stdin")
    parser.add_argument("--normalize", action="store_true", help="mask host bits instead of rejecting them")
    parser.add_argument("--json", action="store_true", help="emit a JSON array")
    args = parser.parse_args(argv)
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        networks = collapse(data.decode("utf-8-sig"), args.normalize)
        output = json.dumps(networks) + "\n" if args.json else "".join(n + "\n" for n in networks)
        sys.stdout.write(output)
    except BrokenPipeError:
        return 0
    except (OSError, ValueError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
