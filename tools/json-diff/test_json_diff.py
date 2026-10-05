import contextlib
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import json_diff as tool


class JsonDiffTests(unittest.TestCase):
    def test_object_order_and_numeric_equivalence(self):
        self.assertEqual(tool.compare({"b": 2, "a": Decimal("1.0")}, {"a": 1, "b": 2}), [])

    def test_nested_operations_and_missing_null(self):
        changes = tool.compare({"x": {"n": 1}, "gone": None}, {"x": {"n": 2}, "new": None})
        self.assertEqual([(c["op"], c["path"]) for c in changes],
                         [("remove", "/gone"), ("add", "/new"), ("replace", "/x/n")])

    def test_pointer_escaping_unicode_and_root(self):
        self.assertEqual(tool.compare({"~/猫": 1}, {"~/猫": 2})[0]["path"], "/~0~1猫")
        self.assertEqual(tool.compare(None, {})[0]["path"], "")

    def test_boolean_is_not_number(self):
        self.assertEqual(tool.compare(True, 1)[0]["op"], "replace")

    def test_array_position_and_tail(self):
        self.assertEqual([c["path"] for c in tool.compare([1, 2], [2, 1, 3])], ["/0", "/1", "/2"])
        self.assertEqual(tool.compare([1, 2], [1])[0]["op"], "remove")

    def test_decimal_precision(self):
        with patch("sys.stdin", io.StringIO('0.123456789012345678901')):
            value = tool.read_json("-")
        self.assertEqual(tool.encode(value), "0.123456789012345678901")
        self.assertTrue(tool.compare(value, Decimal("0.123456789012345678902")))
        self.assertEqual(tool.encode(Decimal("1e400")), "1E+400")

    def test_bad_inputs(self):
        for raw in ['{"a":1,"a":2}', 'NaN', 'Infinity', '{bad', '']:
            with self.subTest(raw=raw), patch("sys.stdin", io.StringIO(raw)):
                with self.assertRaises(ValueError):
                    tool.read_json("-")

    def test_cli_exit_codes_and_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            before, after = Path(folder) / "a.json", Path(folder) / "b.json"
            before.write_text('\ufeff{"x":1}', encoding="utf-8")
            after.write_text('{"x":2}', encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(tool.main([str(before), str(after), "--json"]), 1)
            self.assertEqual(json.loads(output.getvalue())["changes"][0]["after"], 2)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tool.main([str(before), str(before)]), 0)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(tool.main([str(before), str(after) + ".missing"]), 2)
                self.assertEqual(tool.main(["-", "-"]), 2)

    def test_stdin_and_control_character_safe_output(self):
        with tempfile.TemporaryDirectory() as folder:
            after = Path(folder) / "b.json"
            after.write_text('{"a\\n":2}', encoding="utf-8")
            output = io.StringIO()
            with patch("sys.stdin", io.StringIO('{"a\\n":1}')), contextlib.redirect_stdout(output):
                self.assertEqual(tool.main(["-", str(after)]), 1)
            self.assertEqual(len(output.getvalue().splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
