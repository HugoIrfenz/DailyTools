import csv
import io
import unittest

from csv_fill_down import fill_down


class FillDownTests(unittest.TestCase):
    def run_fill(self, source, *columns):
        destination = io.StringIO(newline="")
        fill_down(io.StringIO(source, newline=""), destination, columns)
        destination.seek(0)
        return list(csv.reader(destination))

    def test_independent_columns_and_leading_blanks(self):
        result = self.run_fill("a,b,c\n,X,1\nY,,\n,Z,3\n,,4\n", "a", "b")
        self.assertEqual(result, [
            ["a", "b", "c"], ["", "X", "1"], ["Y", "X", ""],
            ["Y", "Z", "3"], ["Y", "Z", "4"],
        ])

    def test_multiline_and_whitespace_are_values(self):
        result = self.run_fill('a,b\n"x\ny",1\n,2\n ,3\n,4\n', "a")
        self.assertEqual([row[0] for row in result[1:]], ["x\ny", "x\ny", " ", " "])

    def test_invalid_headers(self):
        for source, message in [("", "required"), ("a,a\n", "duplicate"), ("b\n", "unknown")]:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, message):
                self.run_fill(source, "a")

    def test_ragged_rows(self):
        for row in ("x\n", "x,y,z\n"):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "line 2"):
                self.run_fill("a,b\n" + row, "a")

    def test_unterminated_quote(self):
        with self.assertRaises(csv.Error):
            self.run_fill('a\n"unfinished', "a")
