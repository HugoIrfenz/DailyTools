import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import json_canonicalize as tool


SCRIPT = Path(__file__).with_name("json_canonicalize.py")


class JsonCanonicalizeTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_sorts_keys_recursively(self):
        value = tool.parse_json('{"z":{"b":1,"a":2},"a":0}')
        self.assertEqual(tool.serialize(value, None, False), '{"a":0,"z":{"a":2,"b":1}}')

    def test_compact_arrays(self):
        self.assertEqual(tool.serialize([1, True, None], None, False), "[1,true,null]")

    def test_indent(self):
        self.assertEqual(tool.serialize({"b": 1, "a": 2}, 2, False), '{\n  "a": 2,\n  "b": 1\n}')

    def test_ascii_mode(self):
        self.assertEqual(tool.serialize({"word": "café"}, None, True), '{"word":"caf\\u00e9"}')

    def test_duplicate_key_is_rejected(self):
        with self.assertRaisesRegex(tool.CanonicalizeError, "duplicate object key"):
            tool.parse_json('{"a":1,"a":2}')

    def test_nested_duplicate_key_is_rejected(self):
        with self.assertRaises(tool.CanonicalizeError):
            tool.parse_json('{"outer":{"x":1,"x":2}}')

    def test_nonstandard_numbers_are_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value), self.assertRaises(tool.CanonicalizeError):
                tool.parse_json(value)

    def test_overflowing_float_is_rejected(self):
        with self.assertRaisesRegex(tool.CanonicalizeError, "non-finite"):
            tool.parse_json("1e400")

    def test_top_level_scalar(self):
        self.assertEqual(tool.serialize(tool.parse_json('"ok"'), None, False), '"ok"')

    def test_cli_reads_stdin(self):
        result = self.run_cli("-", data=b'{"b":2,"a":1}')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'{"a":1,"b":2}\n')

    def test_cli_reads_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text('{"two":2,"one":1}', encoding="utf-8")
            result = self.run_cli(str(path), "--indent", "2")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"one": 1, "two": 2})

    def test_cli_rejects_invalid_utf8(self):
        result = self.run_cli("-", data=b"\xff")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)

    def test_cli_rejects_invalid_json(self):
        result = self.run_cli("-", data=b"{")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"invalid JSON", result.stderr)

    def test_cli_reports_unencodable_surrogate(self):
        result = self.run_cli("-", data=b'"\\ud800"')
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"surrogates not allowed", result.stderr)

    def test_cli_rejects_large_indent(self):
        result = self.run_cli("-", "--indent", "17", data=b"{}")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
