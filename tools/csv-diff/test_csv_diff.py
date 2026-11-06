import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_diff import CsvDiffError, compare_csv, parse_csv


SCRIPT = Path(__file__).with_name("csv_diff.py")


class CsvDiffTests(unittest.TestCase):
    def test_reports_added_removed_changed_and_unchanged(self):
        before = "id,name,role\n1,Ana,dev\n2,Bob,qa\n4,Dee,ops\n"
        after = "id,name,role\n1,Ana,lead\n2,Bob,qa\n3,Cam,dev\n"
        report = compare_csv(before, after, ["id"])
        self.assertEqual(
            report["summary"],
            {"added": 1, "removed": 1, "changed": 1, "unchanged": 1},
        )
        self.assertEqual(report["added"][0]["key"], {"id": "3"})
        self.assertEqual(report["removed"][0]["key"], {"id": "4"})
        self.assertEqual(
            report["changed"][0]["fields"],
            {"role": {"before": "dev", "after": "lead"}},
        )

    def test_row_order_does_not_matter(self):
        before = "id,value\n2,b\n1,a\n"
        after = "id,value\n1,a\n2,b\n"
        self.assertEqual(
            compare_csv(before, after, ["id"])["summary"],
            {"added": 0, "removed": 0, "changed": 0, "unchanged": 2},
        )

    def test_header_order_may_differ(self):
        before = "id,name,role\n1,Ana,dev\n"
        after = "role,id,name\ndev,1,Ana\n"
        self.assertEqual(compare_csv(before, after, ["id"])["summary"]["unchanged"], 1)

    def test_composite_key(self):
        before = "team,id,value\na,1,old\nb,1,same\n"
        after = "team,id,value\na,1,new\nb,1,same\n"
        report = compare_csv(before, after, ["team", "id"])
        self.assertEqual(report["changed"][0]["key"], {"team": "a", "id": "1"})

    def test_changed_fields_follow_after_header_order(self):
        before = "id,a,b\n1,old,old\n"
        after = "b,id,a\nnew,1,new\n"
        fields = compare_csv(before, after, ["id"])["changed"][0]["fields"]
        self.assertEqual(list(fields), ["b", "a"])

    def test_quoted_multiline_field(self):
        before = 'id,note\n1,"hello\nworld"\n'
        after = 'id,note\n1,"hello\nthere"\n'
        report = compare_csv(before, after, ["id"])
        self.assertEqual(report["summary"]["changed"], 1)

    def test_unicode_values(self):
        report = compare_csv("id,name\n1,José\n", "id,name\n1,Josée\n", ["id"])
        self.assertEqual(report["changed"][0]["fields"]["name"]["after"], "Josée")

    def test_duplicate_key_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "duplicate key"):
            compare_csv("id,v\n1,a\n1,b\n", "id,v\n1,a\n", ["id"])

    def test_missing_key_column_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "key column not found"):
            compare_csv("id,v\n1,a\n", "id,v\n1,a\n", ["missing"])

    def test_repeated_key_argument_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "must be unique"):
            compare_csv("id,v\n1,a\n", "id,v\n1,a\n", ["id", "id"])

    def test_header_set_difference_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "header sets differ"):
            compare_csv("id,a\n1,x\n", "id,b\n1,x\n", ["id"])

    def test_duplicate_header_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "duplicate header"):
            parse_csv("id,id\n1,2\n", "sample")

    def test_empty_header_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "empty header"):
            parse_csv("id,\n1,x\n", "sample")

    def test_missing_header_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "missing header"):
            parse_csv("", "sample")

    def test_wrong_field_count_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "wrong number"):
            compare_csv("id,v\n1,a,extra\n", "id,v\n1,a\n", ["id"])

    def test_malformed_csv_is_rejected(self):
        with self.assertRaisesRegex(CsvDiffError, "invalid CSV"):
            parse_csv('id,v\n1,"unfinished\n', "sample")

    def test_cli_file_input_and_compact_output(self):
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory, "before.csv")
            after = Path(directory, "after.csv")
            before.write_text("id,v\n1,a\n", encoding="utf-8")
            after.write_text("id,v\n1,b\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(before), str(after), "--key", "id", "--compact"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["summary"]["changed"], 1)
        self.assertEqual(result.stderr, "")

    def test_cli_reads_one_input_from_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            after = Path(directory, "after.csv")
            after.write_text("id,v\n1,a\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "-", str(after), "--key", "id"],
                input="id,v\n1,a\n",
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["summary"]["unchanged"], 1)

    def test_check_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory, "before.csv")
            after = Path(directory, "after.csv")
            before.write_text("id,v\n1,a\n", encoding="utf-8")
            after.write_text("id,v\n1,b\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(before), str(after), "--key", "id", "--check"],
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)

    def test_cli_reads_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory, "before.csv")
            after = Path(directory, "after.csv")
            before.write_bytes(b"\xef\xbb\xbfid,v\n1,a\n")
            after.write_bytes(b"\xef\xbb\xbfid,v\n1,a\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(before), str(after), "--key", "id"],
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
