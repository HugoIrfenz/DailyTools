import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_join import CsvJoinError, join_rows, output_header, read_table, write_csv


SCRIPT = Path(__file__).with_name("csv_join.py")


class CsvJoinTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_inner_join_matches_keys(self) -> None:
        header, rows = join_rows(
            ["id", "name"], [["1", "A"], ["2", "B"]],
            ["id", "score"], [["2", "9"], ["3", "8"]],
            "id", "id", "inner",
        )
        self.assertEqual(header, ["id", "name", "score"])
        self.assertEqual(rows, [["2", "B", "9"]])

    def test_left_join_keeps_unmatched_rows(self) -> None:
        _, rows = join_rows(
            ["id"], [["1"], ["2"]], ["id", "x"], [["2", "yes"]],
            "id", "id", "left",
        )
        self.assertEqual(rows, [["1", ""], ["2", "yes"]])

    def test_full_join_keeps_right_key(self) -> None:
        _, rows = join_rows(
            ["id", "name"], [["1", "A"]], ["key", "value"], [["2", "B"]],
            "id", "key", "full",
        )
        self.assertEqual(rows, [["1", "A", ""], ["2", "", "B"]])

    def test_duplicate_keys_create_all_matches(self) -> None:
        _, rows = join_rows(
            ["id"], [["1"]], ["id", "x"], [["1", "a"], ["1", "b"]],
            "id", "id", "inner",
        )
        self.assertEqual(rows, [["1", "a"], ["1", "b"]])

    def test_header_collisions_receive_right_prefix(self) -> None:
        self.assertEqual(
            output_header(["id", "name"], ["id", "name"], "id"),
            ["id", "name", "right.name"],
        )

    def test_repeated_collision_gets_numeric_prefix(self) -> None:
        self.assertEqual(
            output_header(["id", "name", "right.name"], ["id", "name"], "id")[-1],
            "right2.name",
        )

    def test_missing_left_key_is_rejected(self) -> None:
        with self.assertRaises(CsvJoinError):
            join_rows(["id"], [], ["id"], [], "missing", "id", "inner")

    def test_missing_right_key_is_rejected(self) -> None:
        with self.assertRaises(CsvJoinError):
            join_rows(["id"], [], ["id"], [], "id", "missing", "inner")

    def test_read_table_rejects_duplicate_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "a.csv")
            path.write_text("id,id\n1,2\n", encoding="utf-8")
            with self.assertRaises(CsvJoinError):
                read_table(path)

    def test_read_table_rejects_wrong_row_width(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "a.csv")
            path.write_text("id,name\n1\n", encoding="utf-8")
            with self.assertRaises(CsvJoinError):
                read_table(path)

    def test_read_table_rejects_empty_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "a.csv")
            path.write_text("", encoding="utf-8")
            with self.assertRaises(CsvJoinError):
                read_table(path)

    def test_write_csv_quotes_values(self) -> None:
        output = io.StringIO()
        write_csv(output, ["id", "text"], [["1", "a,b"]], ",")
        self.assertEqual(output.getvalue(), 'id,text\n1,"a,b"\n')

    def test_cli_supports_different_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            left = Path(directory, "left.csv")
            right = Path(directory, "right.csv")
            left.write_text("id,name\n1,A\n", encoding="utf-8")
            right.write_text("user_id,score\n1,9\n", encoding="utf-8")
            result = self.run_cli(str(left), str(right), "--left-key", "id", "--right-key", "user_id")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "id,name,score\n1,A,9\n")

    def test_cli_supports_custom_delimiter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            left = Path(directory, "left.csv")
            right = Path(directory, "right.csv")
            left.write_text("id;name\n1;A\n", encoding="utf-8")
            right.write_text("id;score\n1;9\n", encoding="utf-8")
            result = self.run_cli(str(left), str(right), "--left-key", "id", "--delimiter", ";")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "id;name;score\n1;A;9\n")

    def test_cli_reports_missing_file(self) -> None:
        result = self.run_cli("left.csv", "right.csv", "--left-key", "id")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
