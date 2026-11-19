import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("html_entities.py")


class CLITests(unittest.TestCase):
    def run_cli(self, payload, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_encode_decode(self):
        result = self.run_cli(b'<p title="x">&</p>', "encode", "-")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'&lt;p title=&quot;x&quot;&gt;&amp;&lt;/p&gt;')
        decoded = self.run_cli(result.stdout, "decode", "-")
        self.assertEqual(decoded.stdout, b'<p title="x">&</p>')

    def test_file_bom_numeric_and_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes(b"\xef\xbb\xbf&#128512;&amp;")
            result = self.run_cli(b"", "decode", str(path))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode(), "😀&")

    def test_invalid_utf8(self):
        result = self.run_cli(b"\xff", "encode", "-")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

