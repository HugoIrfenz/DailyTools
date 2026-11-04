import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonl_to_json as tool


SCRIPT = Path(__file__).with_name("jsonl_to_json.py")


class JsonlToJsonTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def test_objects_become_array(self):
        self.assertEqual(tool.parse_lines('{"a":1}\n{"b":2}\n', False), [{"a": 1}, {"b": 2}])

    def test_scalar_records_are_allowed(self):
        self.assertEqual(tool.parse_lines('1\ntrue\nnull\n', False), [1, True, None])

    def test_blank_lines_are_ignored(self):
        self.assertEqual(tool.parse_lines('\n1\n  \n2\n', False), [1, 2])

    def test_blank_lines_can_be_rejected(self):
        with self.assertRaisesRegex(tool.ConvertError, "blank line at line 2"):
            tool.parse_lines('1\n\n2\n', True)

    def test_duplicate_key_is_rejected(self):
        with self.assertRaisesRegex(tool.ConvertError, "line 1"):
            tool.parse_lines('{"a":1,"a":2}\n', False)

    def test_nested_duplicate_key_is_rejected(self):
        with self.assertRaises(tool.ConvertError):
            tool.parse_lines('{"x":{"a":1,"a":2}}\n', False)

    def test_nonstandard_number_is_rejected(self):
        with self.assertRaisesRegex(tool.ConvertError, "non-standard"):
            tool.parse_lines('NaN\n', False)

    def test_overflowing_float_is_rejected(self):
        with self.assertRaisesRegex(tool.ConvertError, "non-finite"):
            tool.parse_lines('1e400\n', False)

    def test_error_reports_physical_line(self):
        with self.assertRaisesRegex(tool.ConvertError, "line 3"):
            tool.parse_lines('1\n\n{\n', False)

    def test_empty_input_produces_empty_array(self):
        self.assertEqual(tool.parse_lines('', False), [])

    def test_cli_reads_stdin_compact(self):
        result = self.run_cli("-", data=b'{"a":1}\n{"a":2}\n')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'[{"a":1},{"a":2}]\n')

    def test_cli_reads_bom_file_and_indents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            path.write_bytes(b'\xef\xbb\xbf{"a":1}\n')
            result = self.run_cli(str(path), "--indent", "2")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), [{"a": 1}])

    def test_cli_rejects_invalid_utf8(self):
        result = self.run_cli("-", data=b"\xff\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)

    def test_cli_rejects_bad_indent(self):
        result = self.run_cli("-", "--indent", "17", data=b"1\n")
        self.assertEqual(result.returncode, 2)

    def test_unicode_is_written_as_utf8(self):
        result = self.run_cli("-", data='"café"\n'.encode())
        self.assertEqual(result.stdout, '["café"]\n'.encode())


if __name__ == "__main__":
    unittest.main()
