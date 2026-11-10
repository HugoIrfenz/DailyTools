import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from csv_transpose import transpose

SCRIPT = Path(__file__).with_name("csv_transpose.py")


class TransposeTests(unittest.TestCase):
    def test_rectangle(self):
        self.assertEqual(transpose('name,Ada,Lin\nscore,8,9\n'), 'name,score\r\nAda,8\r\nLin,9\r\n')

    def test_empty(self):
        self.assertEqual(transpose(''), '')

    def test_single(self):
        self.assertEqual(transpose('one'), 'one\r\n')

    def test_empty_fields(self):
        self.assertEqual(transpose('a,\nb,\n'), 'a,b\r\n,\r\n')

    def test_multiline(self):
        output = transpose('"a\nb",c\r\n"d\re",f\r\n')
        self.assertEqual(list(csv.reader(io.StringIO(output, newline=''))), [['a\nb', 'd\re'], ['c', 'f']])

    def test_quotes(self):
        self.assertEqual(transpose('"a,b","x""y"\n'), '"a,b"\r\n"x""y"\r\n')

    def test_tab_unicode(self):
        self.assertEqual(transpose('雪\t2\na\t3', '\t'), '雪\ta\r\n2\t3\r\n')

    def test_roundtrip_fields(self):
        source = 'a,b,c\n1,2,3\n'
        self.assertEqual(list(csv.reader(io.StringIO(transpose(transpose(source))))),
                         list(csv.reader(io.StringIO(source))))

    def test_invalid(self):
        for text in ('\n', 'a,b\n\n', 'a,b\nc\n', '"unclosed', '"a"x,b', 'a,\x00b'):
            with self.subTest(text=text), self.assertRaises((ValueError, csv.Error)):
                transpose(text)

    def test_bad_delimiter(self):
        for delimiter in ('', 'ab', '\n', '\r', '\x00', '"'):
            with self.subTest(delimiter=delimiter), self.assertRaises(ValueError):
                transpose('a,b', delimiter)

    def test_cli_bom(self):
        run = subprocess.run([sys.executable, str(SCRIPT), '-'], input=b'\xef\xbb\xbfa,b\n1,2', capture_output=True)
        self.assertEqual((run.returncode, run.stdout), (0, b'a,1\r\nb,2\r\n'))

    def test_cli_errors(self):
        for data in (b'a,b\nc', b'\xff', b'"bad'):
            run = subprocess.run([sys.executable, str(SCRIPT), '-'], input=data, capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (1, b''))
            self.assertNotIn(b'Traceback', run.stderr)

    def test_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.csv'
            path.write_text('a,b', encoding='utf-8')
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (0, b'a\r\nb\r\n'))

    def test_usage(self):
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT)], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
