from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import json_select as tool

SCRIPT = Path(__file__).with_name("json_select.py")


class JsonSelectTests(unittest.TestCase):
    def cli(self, *args, raw=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              input=raw, capture_output=True)

    def test_nested_objects_and_array_index(self):
        document = tool.parse_document(b'{"users":[{"name":"Ada"}]}')
        self.assertEqual(tool.select(document, ["users", 0, "name"]), "Ada")

    def test_special_keys_empty_key_and_numeric_key(self):
        document = tool.parse_document(b'{"a.b":{"/~":[]}, "":{"0":"yes"}}')
        self.assertEqual(tool.select(document, ["a.b", "/~"]), [])
        self.assertEqual(tool.select(document, ["", "0"]), "yes")
        with self.assertRaises(tool.MissingPath):
            tool.select(document, ["", 0])

    def test_null_false_and_empty_values_are_found(self):
        document = tool.parse_document(b'{"n":null,"f":false,"a":[],"s":""}')
        self.assertEqual(tool.encode(tool.select(document, ["n"])), "null")
        self.assertEqual(tool.encode(tool.select(document, ["f"])), "false")
        self.assertEqual(tool.select(document, ["s"]), "")
        self.assertEqual(tool.select(document, ["a"]), [])

    def test_empty_path_preserves_root_value(self):
        for raw in (b'null', b'true', b'"hi"', b'[1,2]', b'{}'):
            document = tool.parse_document(raw)
            self.assertIs(tool.select(document, []), document)

    def test_exact_decimal_large_integer_and_exponent(self):
        raw = b'[9007199254740993,0.12345678901234567890123456789,1e400,-0.0]'
        document = tool.parse_document(raw)
        rendered = tool.encode(document)
        self.assertIn("9007199254740993", rendered)
        self.assertEqual(tool.parse_document(rendered.encode()), document)
        self.assertEqual(document[1], Decimal("0.12345678901234567890123456789"))
        self.assertNotIn("Infinity", rendered)

    def test_unicode_and_escaped_strings_roundtrip(self):
        raw = '{"猫":"hello\\nworld \\"quote\\""}'.encode()
        document = tool.parse_document(raw)
        self.assertEqual(tool.parse_document(tool.encode(document).encode()), document)

    def test_invalid_path_types(self):
        for raw in ('{}', '["x",-1]', '[true]', '[0.0]', '[null]', '"x"'):
            with self.subTest(path=raw), self.assertRaises(ValueError):
                tool.parse_path(raw)

    def test_missing_out_of_bounds_and_wrong_container(self):
        document = tool.parse_document(b'{"a":[1]}')
        for path in (["missing"], ["a", 1], ["a", "0"], ["a", 0, "x"]):
            with self.subTest(path=path), self.assertRaises(tool.MissingPath):
                tool.select(document, path)

    def test_duplicate_keys_constants_and_malformed_input(self):
        for raw in (b'{"a":1,"a":2}', b'NaN', b'Infinity', b'{"a":}', b'{} {}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                tool.parse_document(raw)

    def test_cli_stdin_and_missing_distinct_from_null(self):
        good = self.cli("-", '["n"]', raw=b'{"n":null}')
        self.assertEqual(good.returncode, 0)
        self.assertEqual(good.stdout, b'null\n')
        missing = self.cli("-", '["missing"]', raw=b'{"n":null}')
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(missing.stdout, b'')

    def test_cli_file_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "api.json"
            raw = b'{"items":[1,2]}'
            path.write_bytes(raw)
            result = self.cli(path, '["items",1]')
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b'2\n')
            self.assertEqual(path.read_bytes(), raw)

    def test_cli_byte_limit_invalid_utf8_and_argument(self):
        self.assertEqual(self.cli("-", "[]", "--max-bytes", "2", raw=b'null').returncode, 2)
        exact = self.cli("-", "[]", "--max-bytes", "4", raw=b'null')
        self.assertEqual(exact.returncode, 0)
        for args, raw in ((("-", "[]"), b'\xff'), (("-", "bad"), b'{}'),
                          (("-", "[]", "--max-bytes", "0"), b'{}')):
            result = self.cli(*args, raw=raw)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')


if __name__ == "__main__":
    unittest.main()
