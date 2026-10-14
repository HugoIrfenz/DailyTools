import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import query_decode as tool

SCRIPT = Path(__file__).with_name("query_decode.py")


class QueryDecodeTests(unittest.TestCase):
    def cli(self, *args, raw=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              input=raw, capture_output=True)

    def test_order_duplicate_and_empty_values(self):
        self.assertEqual(tool.decode("tag=a&tag=b&flag&empty="), [
            {"name": "tag", "value": "a"}, {"name": "tag", "value": "b"},
            {"name": "flag", "value": ""}, {"name": "empty", "value": ""}])

    def test_plus_space_percent_unicode(self):
        self.assertEqual(tool.decode("q=hello+world&cat=%E7%8C%AB&plus=%2B")[1],
                         {"name": "cat", "value": "猫"})
        self.assertEqual(tool.decode("q=hello+world")[0]["value"], "hello world")
        self.assertEqual(tool.decode("plus=%2B")[0]["value"], "+")

    def test_encoded_delimiters_not_split(self):
        self.assertEqual(tool.decode("a%26b=x%3Dy%26z"),
                         [{"name": "a&b", "value": "x=y&z"}])

    def test_question_mark_empty_name_empty_query(self):
        self.assertEqual(tool.decode("?=x"), [{"name": "", "value": "x"}])
        self.assertEqual(tool.decode(""), [])
        self.assertEqual(tool.decode("?"), [])

    def test_first_equals_and_semicolon_value(self):
        self.assertEqual(tool.decode("a=b=c;d"), [{"name": "a", "value": "b=c;d"}])

    def test_malformed_percent_escapes(self):
        for query in ("a=%", "a=%2", "a=%GG"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                tool.decode(query)

    def test_invalid_percent_utf8_and_raw_controls(self):
        for query in ("a=%FF", "a=%E7", "a=\n"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                tool.decode(query)

    def test_field_limit(self):
        self.assertEqual(len(tool.decode("a=1&b=2", 2)), 2)
        with self.assertRaises(ValueError):
            tool.decode("a=1&b=2", 1)

    def test_cli_stdin_and_terminal_newline(self):
        result = self.cli("-", raw=b'tag=a&tag=b\r\n')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(json.loads(result.stdout)), 2)

    def test_cli_file_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "query.txt"
            path.write_bytes(b'q=hello+world')
            result = self.cli(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)[0]["value"], "hello world")
            self.assertEqual(path.read_bytes(), b'q=hello+world')

    def test_cli_errors_no_partial_output(self):
        for raw in (b'a=%FF', b'a=\xff', b'a=%'):
            result = self.cli("-", raw=raw)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')
        self.assertEqual(self.cli("-", "--max-fields", "0").returncode, 2)
        self.assertEqual(self.cli("-", "--max-fields", "bad").returncode, 2)


if __name__ == "__main__":
    unittest.main()
