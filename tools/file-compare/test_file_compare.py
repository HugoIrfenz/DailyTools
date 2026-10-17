import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from file_compare import CHUNK_SIZE, compare_files, compare_streams

SCRIPT = Path(__file__).with_name("file_compare.py")


class CompareTests(unittest.TestCase):
    def offset(self, a, b, chunk=3):
        return compare_streams(io.BytesIO(a), io.BytesIO(b), chunk)

    def test_empty_equal(self):
        self.assertIsNone(self.offset(b"", b""))

    def test_binary_equal(self):
        self.assertIsNone(self.offset(bytes(range(256)), bytes(range(256))))

    def test_first_and_later_difference(self):
        self.assertEqual(self.offset(b"abc", b"xbc"), 0)
        self.assertEqual(self.offset(b"abcdefg", b"abcdefX"), 6)

    def test_prefix_in_either_direction(self):
        self.assertEqual(self.offset(b"abc", b"abcde"), 3)
        self.assertEqual(self.offset(b"abcde", b"abc"), 3)
        self.assertEqual(self.offset(b"", b"x"), 0)

    def test_actual_chunk_boundary(self):
        prefix = b"x" * CHUNK_SIZE
        self.assertEqual(self.offset(prefix + b"a", prefix + b"b", CHUNK_SIZE),
                         CHUNK_SIZE)

    def test_invalid_chunk(self):
        with self.assertRaises(ValueError):
            self.offset(b"", b"", 0)

    def test_same_file_and_sizes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data"
            path.write_bytes(b"abc")
            self.assertEqual(compare_files(path, path), {
                "equal": True, "first_difference": None,
                "left_bytes": 3, "right_bytes": 3})

    def test_cli_json_difference_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            left, right = Path(folder) / "a", Path(folder) / "b"
            left.write_bytes(b"a\x00b")
            right.write_bytes(b"a\xffb")
            run = subprocess.run([sys.executable, str(SCRIPT), str(left), str(right),
                                  "--json"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads(run.stdout)["first_difference"], 1)
            self.assertEqual(left.read_bytes(), b"a\x00b")
            self.assertEqual(right.read_bytes(), b"a\xffb")

    def test_cli_equal_and_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "a"
            path.write_bytes(b"x")
            for other, code in [(path, 0), (Path(folder), 2), (path / "missing", 2)]:
                run = subprocess.run([sys.executable, str(SCRIPT), str(path), str(other)],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, code)
                if code == 2:
                    self.assertEqual(run.stdout, "")
                    self.assertTrue(run.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFO")
    def test_fifo_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as folder:
            fifo = Path(folder) / "pipe"
            os.mkfifo(fifo)
            with self.assertRaises(ValueError):
                compare_files(fifo, fifo)


if __name__ == "__main__":
    unittest.main()
