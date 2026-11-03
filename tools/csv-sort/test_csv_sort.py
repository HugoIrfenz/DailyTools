import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import csv_sort as tool


SCRIPT = Path(__file__).with_name("csv_sort.py")


class CsvSortTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )

    def test_text_sort(self):
        rows = tool.sort_rows(["name"], [["Zed"], ["Ana"]], ["name"], False, False, False)
        self.assertEqual(rows, [["Ana"], ["Zed"]])

    def test_numeric_sort(self):
        rows = tool.sort_rows(["n"], [["10"], ["2"], ["-1"]], ["n"], True, False, False)
        self.assertEqual(rows, [["-1"], ["2"], ["10"]])

    def test_multiple_keys(self):
        rows = tool.sort_rows(
            ["team", "score"], [["b", "1"], ["a", "2"], ["a", "1"]],
            ["team", "score"], False, False, False
        )
        self.assertEqual(rows, [["a", "1"], ["a", "2"], ["b", "1"]])

    def test_reverse(self):
        rows = tool.sort_rows(["n"], [["1"], ["3"], ["2"]], ["n"], True, False, True)
        self.assertEqual(rows, [["3"], ["2"], ["1"]])

    def test_ignore_case_is_stable(self):
        rows = tool.sort_rows(
            ["name", "id"], [["a", "1"], ["A", "2"], ["b", "3"]],
            ["name"], False, True, False
        )
        self.assertEqual(rows[:2], [["a", "1"], ["A", "2"]])

    def test_equal_keys_retain_source_order(self):
        rows = tool.sort_rows(["k", "id"], [["x", "2"], ["x", "1"]], ["k"], False, False, False)
        self.assertEqual(rows, [["x", "2"], ["x", "1"]])

    def test_duplicate_header_rejected(self):
        with self.assertRaisesRegex(tool.SortError, "duplicate CSV header"):
            tool.sort_rows(["a", "a"], [], ["a"], False, False, False)

    def test_unknown_key_rejected(self):
        with self.assertRaisesRegex(tool.SortError, "unknown sort key"):
            tool.sort_rows(["a"], [], ["b"], False, False, False)

    def test_repeated_key_rejected(self):
        with self.assertRaisesRegex(tool.SortError, "must not be repeated"):
            tool.sort_rows(["a"], [], ["a", "a"], False, False, False)

    def test_wrong_row_width_rejected(self):
        with self.assertRaisesRegex(tool.SortError, "row 2"):
            tool.sort_rows(["a", "b"], [["x"]], ["a"], False, False, False)

    def test_invalid_numeric_rejected_without_value(self):
        with self.assertRaises(tool.SortError) as context:
            tool.sort_rows(["n"], [["private"]], ["n"], True, False, False)
        self.assertNotIn("private", str(context.exception))

    def test_nonfinite_numeric_rejected(self):
        with self.assertRaisesRegex(tool.SortError, "non-finite"):
            tool.sort_rows(["n"], [["NaN"]], ["n"], True, False, False)

    def test_render_quotes_fields(self):
        output = tool.render_csv(["name"], [["a,b"]], ",")
        self.assertEqual(output, 'name\n"a,b"\n')

    def test_cli_stdin(self):
        result = self.run_cli("-", "--key", "id", "--numeric", data=b"id,name\n10,A\n2,B\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"id,name\n2,B\n10,A\n")

    def test_cli_file_with_custom_delimiter(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text("name;id\nZ;2\nA;1\n", encoding="utf-8")
            result = self.run_cli(str(path), "--delimiter", ";", "--key", "name")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"name;id\nA;1\nZ;2\n")

    def test_cli_invalid_utf8(self):
        result = self.run_cli("-", "--key", "a", data=b"a\n\xff\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)

    def test_cli_empty_csv(self):
        result = self.run_cli("-", "--key", "a", data=b"")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"CSV is empty", result.stderr)

    def test_cli_quoted_multiline_field(self):
        data = b'id,note\n2,"z\nline"\n1,"a\nline"\n'
        result = self.run_cli("-", "--key", "id", "--numeric", data=data)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith(b'id,note\n1,"a\nline"\n'))


if __name__ == "__main__":
    unittest.main()
