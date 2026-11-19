import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("text_count.py")


class CLITests(unittest.TestCase):
    def run_cli(self, payload, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_unicode_combining_and_crlf(self):
        import json
        result = self.run_cli("é e\u0301\r\n".encode(), "-")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"bytes": 8, "code_points": 6, "words": 2, "lines": 1})

    def test_empty_and_unterminated_file(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            for payload, expected in ((b"", 0), (b"hi", 1)):
                path.write_bytes(payload)
                result = self.run_cli(b"", str(path))
                self.assertEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["lines"], expected)

    def test_invalid_utf8(self):
        result = self.run_cli(b"\xff", "-")
        self.assertEqual((result.returncode, result.stdout), (1, b""))

