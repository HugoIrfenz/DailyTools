import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_aggregate import AggregateError, aggregate_csv

SCRIPT = Path(__file__).with_name("csv_aggregate.py")

class CsvAggregateTests(unittest.TestCase):
    def test_grouped_sum_average_and_count(self):
        source = "team,amount\na,2\nb,4\na,6\n"
        self.assertEqual(aggregate_csv(source, ["team"], [("sum", "amount"), ("avg", "amount")]), "team,count,sum_amount,avg_amount\na,2,8,4\nb,1,4,4\n")
    def test_multiple_group_columns(self):
        result = aggregate_csv("team,region,n\na,e,2\na,w,3\na,e,4\n", ["team", "region"], [("sum", "n")])
        self.assertEqual(result.splitlines()[1:], ["a,e,2,6", "a,w,1,3"])
    def test_global_aggregate_without_group_columns(self):
        self.assertEqual(aggregate_csv("n\n2\n3\n", [], [("sum", "n")]), "count,sum_n\n2,5\n")
    def test_empty_numeric_cells_are_ignored(self):
        self.assertEqual(aggregate_csv("g,n\na,\na,2\n", ["g"], [("avg", "n")]), "g,count,avg_n\na,2,2\n")
    def test_all_empty_numeric_group_emits_blank(self):
        self.assertEqual(aggregate_csv("g,n\na,\n", ["g"], [("sum", "n")]), "g,count,sum_n\na,1,\n")
    def test_min_and_max(self):
        self.assertEqual(aggregate_csv("n\n-2\n5\n1\n", [], [("min", "n"), ("max", "n")]), "count,min_n,max_n\n3,-2,5\n")
    def test_decimal_precision(self):
        self.assertEqual(aggregate_csv("n\n0.1\n0.2\n", [], [("sum", "n"), ("avg", "n")]), "count,sum_n,avg_n\n2,0.3,0.15\n")
    def test_group_order_is_first_seen(self):
        result = aggregate_csv("g,n\nb,1\na,2\nb,3\n", ["g"], [])
        self.assertEqual(result.splitlines()[1:], ["b,2", "a,1"])
    def test_delimiter_semicolon(self):
        self.assertEqual(aggregate_csv("g;n\na;2\n", ["g"], [("sum", "n")], ";"), "g;count;sum_n\na;1;2\n")
    def test_csv_quoting(self):
        self.assertEqual(aggregate_csv('g,n\n"north, west",2\n', ["g"], [("sum", "n")]), 'g,count,sum_n\n"north, west",1,2\n')
    def test_missing_column_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "unknown column"):
            aggregate_csv("g,n\na,1\n", ["missing"], [])
    def test_duplicate_header_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "unique"):
            aggregate_csv("g,g\na,b\n", ["g"], [])
    def test_wrong_row_width_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "row 2.*field count"):
            aggregate_csv("g,n\na,1,extra\n", ["g"], [])
    def test_invalid_decimal_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "not a decimal"):
            aggregate_csv("n\nnope\n", [], [("sum", "n")])
    def test_non_finite_decimal_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "finite"):
            aggregate_csv("n\nNaN\n", [], [("sum", "n")])
    def test_duplicate_metric_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "unique"):
            aggregate_csv("n\n1\n", [], [("sum", "n"), ("sum", "n")])
    def test_generated_output_header_collision_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "output column names"):
            aggregate_csv("count,n\n1,2\n", ["count"], [])
    def test_empty_file_is_rejected(self):
        with self.assertRaisesRegex(AggregateError, "header"):
            aggregate_csv("", [], [])
    def test_cli_stdin(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--group-by", "g", "--sum", "n"], input="g,n\na,2\na,3\n", text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "g,count,sum_n\na,2,5\n")
    def test_cli_reads_utf8_bom_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "input.csv")
            path.write_bytes(b"\xef\xbb\xbfg,n\na,2\n")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--group-by", "g", "--sum", "n"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "g,count,sum_n\na,1,2\n")
    def test_cli_error_exit_code(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--sum", "missing"], input="n\n1\n", text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown column", result.stderr)

if __name__ == "__main__":
    unittest.main()
