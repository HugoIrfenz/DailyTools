import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("url_defang.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_https_and_ipv4(self):
        result = self.run_cli("-", payload=b"https://example.com/a.js?q=1.2\nhttp://127.0.0.1/\n")
        self.assertEqual((result.returncode, result.stdout),
                         (0, b"hxxps://example[.]com/a[.]js?q=1[.]2\nhxxp://127[.]0[.]0[.]1/\n"))

    def test_file_bom_ipv6_and_blank(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "urls.txt"
            path.write_bytes(b"\xef\xbb\xbfhttps://[::1]/\n\n")
            result = self.run_cli(str(path))
        self.assertEqual((result.returncode, result.stdout), (0, b"hxxps://[::1]/\n"))

    def test_invalid_has_no_partial_output(self):
        for value in (b"ftp://example.com", b"https:///path", b"https://exa mple.com", b"https://[bad]/"):
            result = self.run_cli("-", payload=b"https://example.com\n" + value)
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"line 2", result.stderr)

