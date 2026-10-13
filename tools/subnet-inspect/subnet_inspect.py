#!/usr/bin/env python3
"""Inspect an IPv4/IPv6 CIDR and optionally check address membership."""

import argparse
import ipaddress
import json
import sys


def parse_network(value, normalize=False):
    if "/" not in value or "%" in value:
        raise ValueError("use a CIDR address/prefix without a zone identifier")
    return ipaddress.ip_network(value, strict=not normalize)


def inspect(network, addresses=()):
    checks = []
    for raw in addresses:
        if "%" in raw:
            raise ValueError("zone identifiers are not supported")
        address = ipaddress.ip_address(raw)
        checks.append({"address": str(address),
                       "in_network": address.version == network.version and address in network})
    return {
        "network": str(network),
        "version": network.version,
        "prefix_length": network.prefixlen,
        "netmask": str(network.netmask),
        "first_address": str(network.network_address),
        "last_address": str(network.broadcast_address),
        "total_addresses": network.num_addresses,
        "checks": checks,
        "ok": all(check["in_network"] for check in checks),
    }


def text_report(report):
    lines = [
        f"Network: {report['network']} (IPv{report['version']})",
        f"Netmask: {report['netmask']}",
        f"Range: {report['first_address']} - {report['last_address']}",
        f"Total addresses: {report['total_addresses']}",
    ]
    for check in report["checks"]:
        status = "inside" if check["in_network"] else "outside"
        lines.append(f"{check['address']}: {status}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cidr", help="IPv4/IPv6 address with prefix length")
    parser.add_argument("--normalize", action="store_true",
                        help="clear host bits instead of rejecting them")
    parser.add_argument("--contains", action="append", default=[], metavar="IP",
                        help="check a literal IP address; repeat for multiple addresses")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    try:
        network = parse_network(args.cidr, args.normalize)
        report = inspect(network, args.contains)
    except ValueError:
        parser.error("invalid CIDR or IP address; host bits require --normalize; zones are unsupported")
    print(json.dumps(report, separators=(",", ":")) if args.json else text_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
