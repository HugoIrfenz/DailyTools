import json
from pathlib import Path
import subprocess
import sys
import unittest

import subnet_inspect as tool

SCRIPT = Path(__file__).with_name("subnet_inspect.py")


class SubnetInspectTests(unittest.TestCase):
    def report(self, cidr, *addresses, normalize=False):
        return tool.inspect(tool.parse_network(cidr, normalize), addresses)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_ipv4_range_netmask_count(self):
        report = self.report("192.0.2.0/24")
        self.assertEqual(report["first_address"], "192.0.2.0")
        self.assertEqual(report["last_address"], "192.0.2.255")
        self.assertEqual(report["total_addresses"], 256)
        self.assertEqual(report["netmask"], "255.255.255.0")

    def test_ipv4_boundary_membership(self):
        report = self.report("192.0.2.0/24", "192.0.2.0", "192.0.2.255", "192.0.3.0")
        self.assertEqual([x["in_network"] for x in report["checks"]], [True, True, False])
        self.assertFalse(report["ok"])

    def test_ipv4_zero_prefix_and_small_networks(self):
        self.assertEqual(self.report("0.0.0.0/0")["total_addresses"], 2**32)
        self.assertEqual(self.report("192.0.2.0/31")["total_addresses"], 2)
        single = self.report("192.0.2.7/32")
        self.assertEqual(single["first_address"], single["last_address"])

    def test_ipv6_range_and_large_count_without_enumeration(self):
        report = self.report("2001:db8::/32")
        self.assertEqual(report["total_addresses"], 2**96)
        self.assertEqual(report["last_address"], "2001:db8:ffff:ffff:ffff:ffff:ffff:ffff")
        self.assertEqual(report["version"], 6)

    def test_ipv6_zero_prefix_and_small_networks(self):
        self.assertEqual(self.report("::/0")["total_addresses"], 2**128)
        self.assertEqual(self.report("2001:db8::/127")["total_addresses"], 2)
        self.assertEqual(self.report("2001:db8::1/128")["total_addresses"], 1)

    def test_mixed_ip_versions_are_outside(self):
        report = self.report("192.0.2.0/24", "::ffff:192.0.2.1")
        self.assertFalse(report["checks"][0]["in_network"])
        self.assertFalse(self.report("2001:db8::/32", "192.0.2.1")["ok"])

    def test_host_bits_rejected_or_normalized(self):
        with self.assertRaises(ValueError):
            tool.parse_network("192.0.2.23/24")
        report = self.report("192.0.2.23/24", normalize=True)
        self.assertEqual(report["network"], "192.0.2.0/24")
        self.assertEqual(self.report("2001:db8::abcd/64", normalize=True)["network"],
                         "2001:db8::/64")

    def test_invalid_prefix_missing_prefix_and_hostname(self):
        for cidr in ("192.0.2.1", "192.0.2.0/33", "::/129", "example.com/24", ""):
            with self.subTest(cidr=cidr), self.assertRaises(ValueError):
                tool.parse_network(cidr)

    def test_zone_identifiers_rejected(self):
        with self.assertRaises(ValueError):
            tool.parse_network("fe80::%eth0/64")
        with self.assertRaises(ValueError):
            self.report("fe80::/64", "fe80::1%eth0")

    def test_ipv6_membership_and_canonical_output(self):
        report = self.report("2001:DB8::/32", "2001:DB8::1", "2001:db9::1")
        self.assertEqual(report["network"], "2001:db8::/32")
        self.assertEqual(report["checks"][0]["address"], "2001:db8::1")
        self.assertEqual([x["in_network"] for x in report["checks"]], [True, False])

    def test_cli_text_and_normalized_json(self):
        result = self.cli("192.0.2.0/24")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Total addresses: 256", result.stdout)
        result = self.cli("192.0.2.7/24", "--normalize", "--contains", "192.0.2.9", "--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["network"], "192.0.2.0/24")

    def test_cli_outside_exit_one_and_invalid_exit_two(self):
        outside = self.cli("192.0.2.0/24", "--contains", "192.0.3.1", "--json")
        self.assertEqual(outside.returncode, 1)
        self.assertFalse(json.loads(outside.stdout)["ok"])
        for args in (("192.0.2.7/24",), ("::/64", "--contains", "hostname"),
                     ("::/129",), ("::/64", "--contains", "fe80::1%eth0")):
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
