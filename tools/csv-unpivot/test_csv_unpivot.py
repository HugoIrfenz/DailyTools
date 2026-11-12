import csv
import io
import unittest

from csv_unpivot import unpivot


class UnpivotTests(unittest.TestCase):
    def test_key_order_multiline_and_blank_value(self):
        output = io.StringIO(newline="")
        unpivot(io.StringIO('id,jan,region,feb\na,"1\n2",west,\n'), output, ["region", "id"])
        self.assertEqual(list(csv.reader(io.StringIO(output.getvalue()))), [
            ["region", "id", "column", "value"],
            ["west", "a", "jan", "1\n2"],
            ["west", "a", "feb", ""],
        ])

    def test_header_only(self):
        output = io.StringIO()
        unpivot(io.StringIO("id,jan\n"), output, ["id"])
        self.assertEqual(output.getvalue(), "id,column,value\r\n")

    def test_rejects_invalid_shapes_and_keys(self):
        for data, keys in (
            ("", ["id"]), ("id,id\n", ["id"]), ("id,\n", ["id"]),
            ("id,jan\n", ["typo"]), ("id,jan\n", ["id", "id"]),
            ("id\n", ["id"]), ("column,x\n", ["column"]),
            ("id,jan\n1\n", ["id"]), ("id,jan\n1,2,3\n", ["id"]),
        ):
            with self.subTest(data=data, keys=keys), self.assertRaises(ValueError):
                unpivot(io.StringIO(data), io.StringIO(), keys)

    def test_rejects_unclosed_quote(self):
        with self.assertRaises(csv.Error):
            unpivot(io.StringIO('id,jan\n1,"2'), io.StringIO(), ["id"])
