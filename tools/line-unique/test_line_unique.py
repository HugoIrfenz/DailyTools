import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import line_unique as tool

SCRIPT = Path(__file__).with_name("line_unique.py")


class LineUniqueTests(unittest.TestCase):
    def run_cli(self, *args, raw=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              input=raw, capture_output=True)

    def test_nonadjacent_duplicates_order_and_counts(self):
        entries, stats = tool.deduplicate(io.BytesIO(b'b\na\nb\nc\na\n'))
        self.assertEqual(entries, [["b", 2], ["a", 2], ["c", 1]])
        self.assertEqual(stats["duplicate_lines"], 2)

    def test_crlf_and_missing_final_newline(self):
        entries, _ = tool.deduplicate(io.BytesIO(b'a\r\nb\na'))
        self.assertEqual(entries, [["a", 2], ["b", 1]])

    def test_unicode_casefold_retains_first_original(self):
        raw = 'Straße\nSTRASSE\n猫\n猫\n'.encode()
        entries, _ = tool.deduplicate(io.BytesIO(raw), ignore_case=True)
        self.assertEqual(entries, [["Straße", 2], ["猫", 2]])

    def test_strip_affects_comparison_only(self):
        entries, _ = tool.deduplicate(io.BytesIO(b'  A \nA\na\n'),
                                     ignore_case=True, strip=True)
        self.assertEqual(entries, [["  A ", 3]])

    def test_defaults_distinguish_case_and_whitespace(self):
        entries, _ = tool.deduplicate(io.BytesIO(b'A\na\n A\n'))
        self.assertEqual(len(entries), 3)

    def test_blank_lines_and_skip_blank_counts(self):
        raw = b'\n \n\nA\n'
        entries, _ = tool.deduplicate(io.BytesIO(raw))
        self.assertEqual(entries, [["", 2], [" ", 1], ["A", 1]])
        entries, stats = tool.deduplicate(io.BytesIO(raw), skip_blank=True)
        self.assertEqual(entries, [["A", 1]])
        self.assertEqual(stats["skipped_blank_lines"], 3)
        self.assertEqual(stats["duplicate_lines"], 0)

    def test_empty_and_bom_input(self):
        self.assertEqual(tool.deduplicate(io.BytesIO(b''))[0], [])
        entries, _ = tool.deduplicate(io.BytesIO(b'\xef\xbb\xbfa\na\n'))
        self.assertEqual(len(entries), 2)

    def test_single_pass_large_repeat_input(self):
        entries, stats = tool.deduplicate((b'x\n' for _ in range(10000)))
        self.assertEqual(entries, [["x", 10000]])
        self.assertEqual(stats["input_lines"], 10000)

    def test_cli_counts_stats_stdin(self):
        result = self.run_cli("-", "--counts", "--stats", raw=b'pear\napple\npear\n')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'2\tpear\n1\tapple\n')
        self.assertEqual(json.loads(result.stderr)["unique_lines"], 2)

    def test_cli_file_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "items.txt"
            raw = b'b\na\nb'
            path.write_bytes(raw)
            result = self.run_cli(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b'b\na\n')
            self.assertEqual(path.read_bytes(), raw)

    def test_invalid_utf8_does_not_emit_partial_output(self):
        result = self.run_cli("-", raw=b'valid\n\xffprivate\n')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertNotIn(b'private', result.stderr)

    def test_missing_file_exit_two(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_cli(Path(folder) / "missing")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')


if __name__ == "__main__":
    unittest.main()
