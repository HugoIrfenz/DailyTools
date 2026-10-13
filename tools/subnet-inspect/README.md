# Subnet Inspect

Show an IPv4/IPv6 CIDR's normalized network, netmask, first/last address, and total address count. Optionally check whether literal IP addresses fall inside it.

Requires Python 3.9+; standard library only. Processing is local and does not resolve DNS or open network connections. Run from the repository root:

```bash
python tools/subnet-inspect/subnet_inspect.py 192.0.2.0/24
python tools/subnet-inspect/subnet_inspect.py 2001:db8::/32 --contains 2001:db8::1 --json
python tools/subnet-inspect/subnet_inspect.py 192.0.2.7/24 --normalize
```

The first command prints:

```text
Network: 192.0.2.0/24 (IPv4)
Netmask: 255.255.255.0
Range: 192.0.2.0 - 192.0.2.255
Total addresses: 256
```

Repeat `--contains IP` to check several addresses. Exit codes: `0` for a valid inspection with all supplied addresses inside, `1` when any address is outside, `2` for invalid input. An address from another IP version is outside.

Limits: a prefix is required; host bits are rejected unless `--normalize` is supplied. Scoped IPv6 addresses (`%eth0`), hostnames, and address ranges are unsupported. Counts include **all** addresses, including IPv4 network/broadcast addresses; no usable-host or reachability claim is made. Large IPv6 networks are calculated arithmetically, not enumerated. JSON integer counts may exceed JavaScript's exact integer range.

Tests:

```bash
python -m unittest discover -s tools/subnet-inspect -v
```

Checks include IPv4/IPv6 boundaries, /0 and single-address networks, mixed versions, host-bit normalization, invalid input, and CLI exit codes.
