# CIDR Collapse

Merge overlapping and adjacent IPv4/IPv6 networks into CIDRs covering the same address set. Remove duplicate and contained networks. Python 3.9+, standard library only; no network requests or firewall changes.

```bash
python tools/cidr-collapse/cidr_collapse.py networks.txt --json
printf '192.0.2.0/25\n192.0.2.128/25\n' | python tools/cidr-collapse/cidr_collapse.py -
```

The example emits `192.0.2.0/24`. Input contains one network or bare IP address per line. Blank lines and whole-line `#` comments are ignored. IPv4 is emitted before IPv6, sorted numerically within each family. UTF-8 BOM is accepted. IPv4 and IPv6 remain separate, including IPv4-mapped IPv6 addresses.

Host bits in CIDRs are rejected unless `--normalize` is set, which masks them to the containing network. Zone identifiers, inline comments, and invalid entries return exit 1 without partial output; argument errors use exit 2. Empty input emits nothing, or `[]` with `--json`. All input networks are held in memory. Redirect to a different file from the input.

```bash
python -m unittest discover -s tools/cidr-collapse -v
```
