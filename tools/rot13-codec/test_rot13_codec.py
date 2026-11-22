import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("rot13_codec.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_round_trip_unicode_and_line_endings(self):
        payload = "Hello é!\r\n".encode()
        result = self.run_cli("-", payload=payload)
        self.assertEqual((result.returncode, result.stdout), (0, "Uryyb é!\r\n".encode()))
        self.assertEqual(self.run_cli("-", payload=result.stdout).stdout, payload)

    def test_file_and_invalid_utf8(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes(b"abc")
            self.assertEqual(self.run_cli(str(path)).stdout, b"nop")
        result = self.run_cli("-", payload=b"\xff")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

