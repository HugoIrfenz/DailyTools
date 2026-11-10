import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from json_to_jsonl import convert

SCRIPT = Path(__file__).with_name("json_to_jsonl.py")


class ConvertTests(unittest.TestCase):
    def test_objects(self):
        self.assertEqual(convert('[{"id":1},{"id":2}]'), '{"id":1}\n{"id":2}\n')

    def test_empty(self):
        self.assertEqual(convert("[]"), "")

    def test_all_types(self):
        data = [None, True, False, 42, "hello", [], {}, [1, {"a": 2}]]
        self.assertEqual([json.loads(x) for x in convert(json.dumps(data)).splitlines()], data)

    def test_precision(self):
        result = convert('[0.12345678901234567890123456789,1e10000,-0.00]')
        self.assertEqual([json.loads(x, parse_float=Decimal) for x in result.splitlines()],
                         [Decimal("0.12345678901234567890123456789"), Decimal("1e10000"), Decimal("-0.00")])

    def test_nested_decimal(self):
        self.assertEqual(convert('[{"x":[1.2300]}]'), '{"x":[1.2300]}\n')

    def test_string_newlines(self):
        self.assertEqual(len(convert('["a\\nb","雪","\\ud800"]').splitlines()), 3)

    def test_invalid(self):
        for text in ('{}', 'null', '1', '[1,]', '[1] extra', '', '[NaN]', '[Infinity]',
                     '[{"x":1,"x":2}]', '[{"a":{"x":1,"x":2}}]'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                convert(text)

    def test_stdin_bom(self):
        run = subprocess.run([sys.executable, str(SCRIPT), '-'], input=b'\xef\xbb\xbf[1,2]', capture_output=True)
        self.assertEqual((run.returncode, run.stdout), (0, b'1\n2\n'))

    def test_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            path.write_text('["ok"]', encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (0, b'"ok"\n'))

    def test_no_partial_output(self):
        for data in (b'[1,NaN]', b'[1,\xff]', b'[{"a":1,"a":2}]', b'[1e9999999999999999999999999]'):
            run = subprocess.run([sys.executable, str(SCRIPT), '-'], input=data, capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (1, b''))
            self.assertNotIn(b'Traceback', run.stderr)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            run = subprocess.run([sys.executable, str(SCRIPT), str(Path(folder) / 'absent')], capture_output=True)
            self.assertEqual(run.returncode, 1)

    def test_usage(self):
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT)], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
