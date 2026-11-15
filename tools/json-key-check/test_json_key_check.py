import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("json_key_check.py")


class KeyCheckTests(unittest.TestCase):
    def run_cli(self, payload, source="-"):
        return subprocess.run([sys.executable, SCRIPT, source], input=payload, capture_output=True)

    def test_nested_duplicate_and_escaped_key(self):
        result = self.run_cli(rb'{"a":[{"k":0,"\u006b":1,"k":2}]}')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b'["a", 0, "k"]\n["a", 0, "k"]\n')

    def test_keys_in_separate_objects_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(b'\xef\xbb\xbf[{"x":1},{"x":2}]')
            result = self.run_cli(b"", path)
        self.assertEqual((result.returncode, result.stdout), (0, b""))

    def test_invalid_input(self):
        for payload in (b'{"a":NaN}', b'{"a":', b'\xff'):
            with self.subTest(payload=payload):
                result = self.run_cli(payload)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"json-key-check:", result.stderr)
