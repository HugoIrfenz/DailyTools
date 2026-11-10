import ipaddress
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from cidr_collapse import collapse

SCRIPT = Path(__file__).with_name("cidr_collapse.py")


class CollapseTests(unittest.TestCase):
    def test_adjacent(self):
        self.assertEqual(collapse('192.0.2.0/25\n192.0.2.128/25'), ['192.0.2.0/24'])

    def test_containment_duplicates(self):
        self.assertEqual(collapse('192.0.2.0/24\n192.0.2.0/25\n192.0.2.0/24'), ['192.0.2.0/24'])

    def test_ipv6(self):
        self.assertEqual(collapse('2001:db8::/127\n2001:db8::2/127'), ['2001:db8::/126'])

    def test_mixed_sorted(self):
        self.assertEqual(collapse('::1\n192.0.2.8\n10.0.0.1'), ['10.0.0.1/32', '192.0.2.8/32', '::1/128'])

    def test_no_widening(self):
        source = ['192.0.2.0/29', '192.0.2.16/29', '192.0.2.8/30']
        addresses = lambda ns: {a for n in ns for a in ipaddress.ip_network(n)}
        self.assertEqual(addresses(collapse('\n'.join(source))), addresses(source))

    def test_nonmergeable_adjacent(self):
        self.assertEqual(collapse('192.0.2.1\n192.0.2.2'), ['192.0.2.1/32', '192.0.2.2/32'])

    def test_default_routes(self):
        self.assertEqual(collapse('0.0.0.0/0\n::/0\n10.0.0.0/8'), ['0.0.0.0/0', '::/0'])

    def test_empty_comments(self):
        self.assertEqual(collapse(' \n # comment\n'), [])

    def test_host_bits(self):
        with self.assertRaises(ValueError):
            collapse('192.0.2.7/24')
        self.assertEqual(collapse('192.0.2.7/24', True), ['192.0.2.0/24'])

    def test_bad_lines(self):
        for text in ('bad', '192.0.2.0/33', '::1/129', '10.0.0.0/8 # comment', 'fe80::%eth0/64'):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'line 2'):
                collapse('# heading\n' + text)

    def test_cli_json_bom(self):
        run = subprocess.run([sys.executable, str(SCRIPT), '-', '--json'], input=b'\xef\xbb\xbf192.0.2.0/25\n192.0.2.128/25', capture_output=True)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(json.loads(run.stdout), ['192.0.2.0/24'])

    def test_cli_normalize(self):
        run = subprocess.run([sys.executable, str(SCRIPT), '-', '--normalize'], input=b'192.0.2.1/24', capture_output=True)
        self.assertEqual((run.returncode, run.stdout), (0, b'192.0.2.0/24\n'))

    def test_cli_errors(self):
        for data in (b'192.0.2.1\nbad', b'\xff'):
            run = subprocess.run([sys.executable, str(SCRIPT), '-'], input=data, capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (1, b''))
            self.assertNotIn(b'Traceback', run.stderr)

    def test_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'networks.txt'
            path.write_text('::1', encoding='utf-8')
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (0, b'::1/128\n'))

    def test_usage(self):
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT)], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
