import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from line_sample import sample_lines


SCRIPT = Path(__file__).with_name("line_sample.py")


class LineSampleTests(unittest.TestCase):
    def lines(self, count=100):
        return b"".join(f"line-{index}\n".encode() for index in range(count))

    def test_returns_requested_count(self):
        selected, total = sample_lines(io.BytesIO(self.lines()), 10, "seed")
        self.assertEqual((len(selected), total), (10, 100))

    def test_same_seed_is_deterministic(self):
        first, _ = sample_lines(io.BytesIO(self.lines()), 10, "seed")
        second, _ = sample_lines(io.BytesIO(self.lines()), 10, "seed")
        self.assertEqual(first, second)

    def test_different_seed_changes_sample(self):
        first, _ = sample_lines(io.BytesIO(self.lines()), 10, "one")
        second, _ = sample_lines(io.BytesIO(self.lines()), 10, "two")
        self.assertNotEqual(first, second)

    def test_sample_retains_source_order(self):
        selected, _ = sample_lines(io.BytesIO(self.lines()), 20, "seed")
        indexes = [index for index, _ in selected]
        self.assertEqual(indexes, sorted(indexes))

    def test_count_larger_than_input_returns_all_lines(self):
        selected, total = sample_lines(io.BytesIO(b"a\nb\n"), 10, "seed")
        self.assertEqual((selected, total), ([(1, b"a\n"), (2, b"b\n")], 2))

    def test_empty_input_returns_empty_sample(self):
        self.assertEqual(sample_lines(io.BytesIO(b""), 3, "seed"), ([], 0))

    def test_preserves_missing_final_newline(self):
        selected, _ = sample_lines(io.BytesIO(b"only line"), 1, "seed")
        self.assertEqual(selected[0][1], b"only line")

    def test_preserves_non_utf8_bytes(self):
        selected, _ = sample_lines(io.BytesIO(b"\xff\n\xfe\n"), 2, "seed")
        self.assertEqual([line for _, line in selected], [b"\xff\n", b"\xfe\n"])

    def test_cli_reads_stdin(self):
        data = self.lines(20)
        result = subprocess.run([sys.executable, str(SCRIPT), "-", "-n", "5", "--seed", "x"], input=data, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stdout.splitlines()), 5)

    def test_cli_is_deterministic(self):
        command = [sys.executable, str(SCRIPT), "-", "-n", "5", "--seed", "x"]
        first = subprocess.run(command, input=self.lines(20), capture_output=True, check=False)
        second = subprocess.run(command, input=self.lines(20), capture_output=True, check=False)
        self.assertEqual(first.stdout, second.stdout)

    def test_cli_shuffle_changes_output_order(self):
        ordered = subprocess.run([sys.executable, str(SCRIPT), "-", "-n", "20", "--seed", "x"], input=self.lines(20), capture_output=True, check=False)
        shuffled = subprocess.run([sys.executable, str(SCRIPT), "-", "-n", "20", "--seed", "x", "--shuffle"], input=self.lines(20), capture_output=True, check=False)
        self.assertCountEqual(ordered.stdout.splitlines(), shuffled.stdout.splitlines())
        self.assertNotEqual(ordered.stdout, shuffled.stdout)

    def test_cli_rejects_zero_count(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "-", "-n", "0"], input=b"a\n", capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"count must be at least 1", result.stderr)

    def test_cli_refuses_same_input_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lines.txt"
            path.write_bytes(b"a\nb\n")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "-n", "1", "-o", str(path)], capture_output=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b"must differ", result.stderr)
            self.assertEqual(path.read_bytes(), b"a\nb\n")


if __name__ == "__main__":
    unittest.main()
