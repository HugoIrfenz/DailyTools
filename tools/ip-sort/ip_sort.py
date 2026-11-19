"""Sort and deduplicate one IP address per line."""
import argparse
import ipaddress
import sys
from pathlib import Path


def sort_addresses(text):
    addresses = set()
    for number, raw in enumerate(text.splitlines(), 1):
        value = raw.strip()
        if not value:
            continue
        if "%" in value:
            raise ValueError(f"line {number}: scoped addresses are unsupported")
        try:
            addresses.add(ipaddress.ip_address(value))
        except ValueError as error:
            raise ValueError(f"line {number}: invalid IP address") from error
    return sorted(addresses, key=lambda address: (address.version, int(address)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        addresses = sort_addresses(data.decode("utf-8-sig"))
        for address in addresses:
            print(address)
    except (OSError, ValueError) as error:
        parser.exit(1, f"ip-sort: {error}\n")


if __name__ == "__main__":
    main()
