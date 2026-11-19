# IP Sort

Sort and deduplicate IPv4 and IPv6 addresses from UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf '10.0.0.10\n::1\n10.0.0.2\n10.0.0.2\n' | python tools/ip-sort/ip_sort.py -
python tools/ip-sort/ip_sort.py addresses.txt
```

The example prints `10.0.0.2`, `10.0.0.10`, then `::1`. IPv4 comes first, with each family sorted numerically. Blank lines are ignored. CIDRs, hostnames, and scoped IPv6 addresses are rejected. Unique addresses are held in memory.
