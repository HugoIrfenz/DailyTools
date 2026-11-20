import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("regex_extract.py")


class ExtractTests(unittest.TestCase):
    def run_cli(self, pattern, payload=b"", path="-", *options):
        return subprocess.run([sys.executable, SCRIPT, pattern, path, *options],
                              input=payload, capture_output=True)

    def test_named_groups_and_unicode_offsets(self):
        result = self.run_cli(r"order=(?P<id>[0-9]+)", "é order=42".encode())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {
            "start": 2, "end": 10, "match": "order=42",
            "groups": ["42"], "named_groups": {"id": "42"},
        })

    def test_optional_groups_and_zero_length(self):
        result = self.run_cli(r"(a)?b", b"b")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["groups"], [None])
        result = self.run_cli(r"(?=a)", b"aa")
        self.assertEqual(result.returncode, 0)
        self.assertEqual([json.loads(line)["start"] for line in result.stdout.splitlines()], [0, 1])

    def test_file_bom_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.txt"
            path.write_bytes(b"\xef\xbb\xbfERROR\r\n")
            result = self.run_cli("error", b"", str(path), "--ignore-case")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["match"], "ERROR")

    def test_no_matches_and_errors(self):
        self.assertEqual((self.run_cli("x", b"y").returncode, self.run_cli("x", b"y").stdout), (0, b""))
        for pattern, payload in (("[", b""), ("x", b"\xff")):
            with self.subTest(pattern=pattern):
                result = self.run_cli(pattern, payload)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(b"regex-extract:", result.stderr)
