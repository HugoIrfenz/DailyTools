import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_select import CSVSelectError, select_csv, selected_indexes


SCRIPT = Path(__file__).with_name("csv_select.py")


class CSVSelectTests(unittest.TestCase):
    def run_select(self, text, columns, **kwargs):
        output = io.StringIO(newline="")
        count = select_csv(io.StringIO(text, newline=""), output, columns, **kwargs)
        return count, output.getvalue()

    def test_selects_and_reorders_columns(self):
        count, result = self.run_select("id,name,email\n1,Ada,a@example.test\n", ["email", "id"])
        self.assertEqual(count, 1)
        self.assertEqual(result, "email,id\na@example.test,1\n")

    def test_preserves_quoted_fields(self):
        _, result = self.run_select('name,note\nAda,"hello, world"\n', ["note"])
        self.assertEqual(result, 'note\n"hello, world"\n')

    def test_custom_input_and_output_delimiters(self):
        _, result = self.run_select("a;b\n1;2\n", ["b", "a"], delimiter=";", output_delimiter="\t")
        self.assertEqual(result, "b\ta\n2\t1\n")

    def test_empty_input_is_rejected(self):
        with self.assertRaisesRegex(CSVSelectError, "empty"):
            self.run_select("", ["a"])

    def test_missing_column_is_rejected(self):
        with self.assertRaisesRegex(CSVSelectError, "missing columns"):
            self.run_select("a,b\n1,2\n", ["c"])

    def test_duplicate_header_is_rejected(self):
        with self.assertRaisesRegex(CSVSelectError, "duplicate header"):
            self.run_select("a,a\n1,2\n", ["a"])

    def test_duplicate_request_is_rejected(self):
        with self.assertRaisesRegex(CSVSelectError, "must be unique"):
            selected_indexes(["a", "b"], ["a", "a"])

    def test_short_row_is_rejected(self):
        with self.assertRaisesRegex(CSVSelectError, "row 2 has 1 fields"):
            self.run_select("a,b\n1\n", ["a"])

    def test_long_row_is_rejected(self):
        with self.assertRaisesRegex(CSVSelectError, "row 2 has 3 fields"):
            self.run_select("a,b\n1,2,3\n", ["a"])

    def test_malformed_quote_is_rejected(self):
        with self.assertRaisesRegex(CSVSelectError, "invalid CSV"):
            self.run_select('a,b\n"unterminated,2\n', ["a"])

    def test_cli_reads_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-", "b"],
            input="a,b\n1,2\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "b\n2\n")

    def test_cli_refuses_same_input_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text("a\n1\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "a", "-o", str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("must differ", result.stderr)
            self.assertEqual(path.read_text(encoding="utf-8"), "a\n1\n")


if __name__ == "__main__":
    unittest.main()
