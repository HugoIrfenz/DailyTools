import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import csv_frequency as tool


SCRIPT = Path(__file__).with_name("csv_frequency.py")


class CsvFrequencyTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )

    def test_counts_and_sorts_values(self):
        result = tool.analyze([["b"], ["a"], ["b"]], ["value"], [], 10, False)
        self.assertEqual(result["columns"][0]["values"], [
            {"value": "b", "count": 2}, {"value": "a", "count": 1}
        ])

    def test_ties_sort_by_value(self):
        result = tool.analyze([["z"], ["a"]], ["value"], [], 10, False)
        self.assertEqual([x["value"] for x in result["columns"][0]["values"]], ["a", "z"])

    def test_top_limit(self):
        result = tool.analyze([["a"], ["b"], ["c"]], ["v"], [], 2, False)
        self.assertEqual(len(result["columns"][0]["values"]), 2)

    def test_selected_column_order(self):
        result = tool.analyze([["1", "x"]], ["id", "kind"], ["kind", "id"], 10, False)
        self.assertEqual([x["name"] for x in result["columns"]], ["kind", "id"])

    def test_empty_value_counted_by_default(self):
        result = tool.analyze([[""]], ["v"], [], 10, False)
        self.assertEqual(result["columns"][0]["values"], [{"value": "", "count": 1}])

    def test_ignore_empty(self):
        result = tool.analyze([[""], ["a"]], ["v"], [], 10, True)
        self.assertEqual(result["columns"][0]["distinct"], 1)

    def test_duplicate_header_rejected(self):
        with self.assertRaisesRegex(tool.FrequencyError, "duplicate CSV header"):
            tool.analyze([], ["a", "a"], [], 10, False)

    def test_empty_header_name_rejected(self):
        with self.assertRaisesRegex(tool.FrequencyError, "empty column"):
            tool.analyze([], ["a", ""], [], 10, False)

    def test_unknown_column_rejected(self):
        with self.assertRaisesRegex(tool.FrequencyError, "unknown column"):
            tool.analyze([], ["a"], ["b"], 10, False)

    def test_duplicate_selection_rejected(self):
        with self.assertRaisesRegex(tool.FrequencyError, "must not be repeated"):
            tool.analyze([], ["a"], ["a", "a"], 10, False)

    def test_wrong_row_width_rejected(self):
        with self.assertRaisesRegex(tool.FrequencyError, "row 2"):
            tool.analyze([["x"]], ["a", "b"], [], 10, False)

    def test_cli_reads_stdin_json(self):
        result = self.run_cli("-", "--column", "city", data=b"id,city\n1,Jakarta\n2,Jakarta\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["columns"][0]["values"][0]["count"], 2)

    def test_cli_custom_delimiter_and_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text("name;team\nA;red\nB;blue\n", encoding="utf-8")
            result = self.run_cli(str(path), "--delimiter", ";", "--column", "team")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["rows"], 2)

    def test_cli_tsv(self):
        result = self.run_cli("-", "--tsv", data=b"v\na\na\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"2\ta", result.stdout)

    def test_tsv_quotes_tabs_in_values(self):
        result = {"rows": 1, "columns": [{
            "name": "v", "distinct": 1,
            "values": [{"value": "a\tb", "count": 1}],
        }]}
        self.assertIn('1\t"a\tb"', tool.render_tsv(result))

    def test_cli_invalid_utf8(self):
        result = self.run_cli("-", data=b"v\n\xff\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)


if __name__ == "__main__":
    unittest.main()
