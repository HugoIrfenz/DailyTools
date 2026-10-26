import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gzip_check import GzipCheckError, format_text, inspect_gzip


SCRIPT = Path(__file__).with_name("gzip_check.py")


class GzipCheckTests(unittest.TestCase):
    def test_reports_sizes_and_digest(self):
        payload = b"hello" * 20
        stats = inspect_gzip(gzip.compress(payload, mtime=0))
        self.assertEqual(stats["uncompressed_bytes"], len(payload))
        self.assertEqual(stats["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertGreater(stats["compressed_bytes"], 0)

    def test_ratio_uses_uncompressed_over_compressed(self):
        payload = b"a" * 1000
        stats = inspect_gzip(gzip.compress(payload, mtime=0))
        self.assertAlmostEqual(stats["size_ratio"], len(payload) / stats["compressed_bytes"])

    def test_empty_payload_is_valid(self):
        stats = inspect_gzip(gzip.compress(b"", mtime=0))
        self.assertEqual(stats["uncompressed_bytes"], 0)

    def test_concatenated_members_are_combined(self):
        data = gzip.compress(b"one", mtime=0) + gzip.compress(b"two", mtime=0)
        self.assertEqual(inspect_gzip(data)["sha256"], hashlib.sha256(b"onetwo").hexdigest())

    def test_rejects_plain_data(self):
        with self.assertRaisesRegex(GzipCheckError, "invalid gzip"):
            inspect_gzip(b"plain text")

    def test_rejects_truncated_data(self):
        with self.assertRaisesRegex(GzipCheckError, "invalid gzip"):
            inspect_gzip(gzip.compress(b"hello", mtime=0)[:-4])

    def test_rejects_bad_crc(self):
        data = bytearray(gzip.compress(b"hello", mtime=0))
        data[-8] ^= 1
        with self.assertRaisesRegex(GzipCheckError, "invalid gzip"):
            inspect_gzip(bytes(data))

    def test_text_format_contains_digest(self):
        text = format_text(inspect_gzip(gzip.compress(b"hello", mtime=0)))
        self.assertIn("SHA-256 (uncompressed):", text)
        self.assertIn("Uncompressed bytes: 5", text)

    def test_cli_json_from_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.gz"
            path.write_bytes(gzip.compress(b"hello", mtime=0))
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--json"], capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["uncompressed_bytes"], 5)

    def test_cli_reads_stdin(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "-"], input=gzip.compress(b"hello", mtime=0), capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"Uncompressed bytes: 5", result.stdout)

    def test_cli_expected_digest_passes(self):
        payload = b"hello"
        result = subprocess.run([sys.executable, str(SCRIPT), "-", "--expect-sha256", hashlib.sha256(payload).hexdigest()], input=gzip.compress(payload, mtime=0), capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)

    def test_cli_expected_digest_fails(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "-", "--expect-sha256", "0" * 64], input=gzip.compress(b"hello", mtime=0), capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"SHA-256 mismatch", result.stderr)

    def test_cli_rejects_bad_expected_digest(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "-", "--expect-sha256", "xyz"], input=gzip.compress(b"hello", mtime=0), capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"64 hexadecimal", result.stderr)


if __name__ == "__main__":
    unittest.main()
