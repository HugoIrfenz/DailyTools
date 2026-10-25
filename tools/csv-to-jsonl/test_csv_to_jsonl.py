import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_to_jsonl import CSVToJSONLError, convert_csv, validate_header


SCRIPT = Path(__file__).with_name("csv_to_jsonl.py")


class CSVToJSONLTests(unittest.TestCase):
    def convert(self, text, delimiter=","):
        output = io.StringIO()
        count = convert_csv(io.StringIO(text, newline=""), output, delimiter)
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        return count, records, output.getvalue()

    def test_converts_rows_to_objects(self):
        count, records, _ = self.convert("id,name\n1,Ada\n2,Lin\n")
        self.assertEqual(count, 2)
        self.assertEqual(records, [{"id": "1", "name": "Ada"}, {"id": "2", "name": "Lin"}])

    def test_preserves_quoted_commas_and_newlines(self):
        _, records, _ = self.convert('id,note\n1,"hello,\nworld"\n')
        self.assertEqual(records[0]["note"], "hello,\nworld")

    def test_preserves_unicode(self):
        _, _, text = self.convert("name,city\nJosé,Jakarta\n")
        self.assertIn("José", text)

    def test_custom_delimiter(self):
        _, records, _ = self.convert("id;name\n1;Ada\n", ";")
        self.assertEqual(records[0], {"id": "1", "name": "Ada"})

    def test_header_only_writes_no_records(self):
        count, records, text = self.convert("id,name\n")
        self.assertEqual((count, records, text), (0, [], ""))

    def test_empty_input_is_rejected(self):
        with self.assertRaisesRegex(CSVToJSONLError, "empty"):
            self.convert("")

    def test_empty_header_name_is_rejected(self):
        with self.assertRaisesRegex(CSVToJSONLError, "empty header"):
            validate_header(["id", ""])

    def test_duplicate_header_is_rejected(self):
        with self.assertRaisesRegex(CSVToJSONLError, "duplicate header"):
            validate_header(["id", "id"])

    def test_short_row_is_rejected(self):
        with self.assertRaisesRegex(CSVToJSONLError, "row 2 has 1 fields"):
            self.convert("id,name\n1\n")

    def test_long_row_is_rejected(self):
        with self.assertRaisesRegex(CSVToJSONLError, "row 2 has 3 fields"):
            self.convert("id,name\n1,Ada,extra\n")

    def test_malformed_quote_is_rejected(self):
        with self.assertRaisesRegex(CSVToJSONLError, "invalid CSV"):
            self.convert('id,name\n1,"Ada\n')

    def test_cli_reads_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input="id,name\n1,Ada\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"id": "1", "name": "Ada"})

    def test_cli_refuses_same_input_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text("id\n1\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "-o", str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("must differ", result.stderr)
            self.assertEqual(path.read_text(encoding="utf-8"), "id\n1\n")


if __name__ == "__main__":
    unittest.main()
