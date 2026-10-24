import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from json_flatten import JSONFlattenError, escape_token, flatten, load_json, write_records


SCRIPT = Path(__file__).with_name("json_flatten.py")


class JSONFlattenTests(unittest.TestCase):
    def test_flattens_nested_objects_and_arrays(self):
        value = {"users": [{"name": "Ada"}, {"name": "Lin"}], "active": True}
        self.assertEqual(
            list(flatten(value)),
            [
                {"path": "/users/0/name", "value": "Ada"},
                {"path": "/users/1/name", "value": "Lin"},
                {"path": "/active", "value": True},
            ],
        )

    def test_escapes_json_pointer_tokens(self):
        self.assertEqual(escape_token("a/b~c"), "a~1b~0c")
        self.assertEqual(list(flatten({"a/b~c": 1}))[0]["path"], "/a~1b~0c")

    def test_root_scalar_has_empty_pointer(self):
        self.assertEqual(list(flatten(42)), [{"path": "", "value": 42}])

    def test_root_null_has_empty_pointer(self):
        self.assertEqual(list(flatten(None)), [{"path": "", "value": None}])

    def test_empty_object_is_a_leaf(self):
        self.assertEqual(list(flatten({"config": {}})), [{"path": "/config", "value": {}}])

    def test_empty_array_is_a_leaf(self):
        self.assertEqual(list(flatten({"items": []})), [{"path": "/items", "value": []}])

    def test_preserves_object_and_array_order(self):
        value = {"z": [2, 1], "a": 0}
        self.assertEqual([item["path"] for item in flatten(value)], ["/z/0", "/z/1", "/a"])

    def test_handles_deep_input_iteratively(self):
        value = 1
        for _ in range(1500):
            value = [value]
        records = list(flatten(value))
        self.assertEqual(records[0]["value"], 1)
        self.assertEqual(records[0]["path"].count("/"), 1500)

    def test_duplicate_keys_are_rejected(self):
        with self.assertRaisesRegex(JSONFlattenError, "duplicate object key"):
            load_json(io.StringIO('{"a":1,"a":2}'), "input")

    def test_nonstandard_number_is_rejected(self):
        with self.assertRaisesRegex(JSONFlattenError, "non-standard"):
            load_json(io.StringIO("NaN"), "input")

    def test_invalid_json_names_source(self):
        with self.assertRaisesRegex(JSONFlattenError, "data.json"):
            load_json(io.StringIO("{"), "data.json")

    def test_writes_json_lines(self):
        output = io.StringIO()
        count = write_records(flatten({"a": 1, "b": "é"}), output, False)
        self.assertEqual(count, 2)
        lines = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(lines[1], {"path": "/b", "value": "é"})

    def test_writes_json_array(self):
        output = io.StringIO()
        count = write_records(flatten([1, 2]), output, True)
        self.assertEqual(count, 2)
        self.assertEqual(json.loads(output.getvalue())[0], {"path": "/0", "value": 1})

    def test_cli_reads_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input='{"a":{"b":1}}',
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"path": "/a/b", "value": 1})

    def test_cli_writes_array_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "flat.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "-", "--array", "-o", str(output)],
                input='{"a":1}',
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), [{"path": "/a", "value": 1}])

    def test_cli_rejects_invalid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input="{",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
