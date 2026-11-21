import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("json_string_codec.py")


class CodecTests(unittest.TestCase):
    def run_cli(self, mode, data, path="-"):
        return subprocess.run([sys.executable, SCRIPT, mode, str(path)], input=data, capture_output=True)

    def test_round_trip_unicode_quotes_and_newlines(self):
        data = 'é "hello"\n\\'.encode()
        encoded = self.run_cli("encode", data)
        self.assertEqual(encoded.returncode, 0)
        decoded = self.run_cli("decode", encoded.stdout)
        self.assertEqual((decoded.returncode, decoded.stdout), (0, data))

    def test_file_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(b'\xef\xbb\xbf"hello\\n"')
            result = self.run_cli("decode", b"", path)
        self.assertEqual((result.returncode, result.stdout), (0, b"hello\n"))

    def test_bad_json_types_and_surrogate(self):
        for payload in (b"{}", b'"bad', b'"\\ud800"', b"\xff"):
            with self.subTest(payload=payload):
                result = self.run_cli("decode", payload)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
