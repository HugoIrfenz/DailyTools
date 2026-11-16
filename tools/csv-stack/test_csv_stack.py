import csv
import io
import tempfile
import unittest
from pathlib import Path

from csv_stack import stack


class StackTests(unittest.TestCase):
    def parse(self, *inputs):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, data in enumerate(inputs):
                path = Path(directory) / f"{index}.csv"
                path.write_bytes(data)
                paths.append(path)
            output = io.StringIO(newline="")
            stack(paths, output)
            return list(csv.reader(io.StringIO(output.getvalue(), newline="")))

    def test_alignment_bom_and_multiline(self):
        self.assertEqual(self.parse(b"\xef\xbb\xbfa,b\n1,2\n", b'b,a\r\n"x\r\ny",3\r\n'),
                         [["a", "b"], ["1", "2"], ["3", "x\r\ny"]])

    def test_rejects_invalid_headers(self):
        for data in (b"", b"a,a\n", b"a,\n", b"a,c\n"):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "header|column"):
                self.parse(b"a,b\n", data)

    def test_rejects_wrong_width(self):
        with self.assertRaisesRegex(ValueError, "line 2: row width"):
            self.parse(b"a,b\n1\n")
