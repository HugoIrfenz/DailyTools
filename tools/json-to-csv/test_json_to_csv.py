import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from json_to_csv import (
    JsonToCsvError,
    convert_rows,
    infer_fields,
    scalar_text,
    unique_object,
    validate_rows,
    write_csv,
)


SCRIPT = Path(__file__).with_name("json_to_csv.py")


class JsonToCsvTests(unittest.TestCase):
    def run_cli(self, *args: str, input_bytes: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_infers_fields_in_first_seen_order(self) -> None:
        rows = [{"id": 1, "name": "A"}, {"name": "B", "score": 9}]
        self.assertEqual(infer_fields(rows), ["id", "name", "score"])

    def test_missing_fields_become_empty_cells(self) -> None:
        fields, rows = convert_rows([{"id": 1}, {"name": "B"}])
        self.assertEqual(fields, ["id", "name"])
        self.assertEqual(rows, [["1", ""], ["", "B"]])

    def test_explicit_fields_set_order_and_ignore_extras(self) -> None:
        fields, rows = convert_rows([{"id": 1, "name": "A", "extra": 2}], ["name", "id"])
        self.assertEqual(fields, ["name", "id"])
        self.assertEqual(rows, [["A", "1"]])

    def test_scalar_conversion(self) -> None:
        self.assertEqual(scalar_text(None, 0, "x"), "")
        self.assertEqual(scalar_text(True, 0, "x"), "true")
        self.assertEqual(scalar_text(False, 0, "x"), "false")
        self.assertEqual(scalar_text(1.5, 0, "x"), "1.5")

    def test_nested_values_are_rejected(self) -> None:
        with self.assertRaises(JsonToCsvError):
            convert_rows([{"nested": {"a": 1}}])
        with self.assertRaises(JsonToCsvError):
            convert_rows([{"nested": [1]}])

    def test_top_level_must_be_array(self) -> None:
        with self.assertRaises(JsonToCsvError):
            validate_rows({"id": 1})

    def test_array_items_must_be_objects(self) -> None:
        with self.assertRaises(JsonToCsvError):
            validate_rows([{"id": 1}, 2])

    def test_duplicate_object_keys_are_rejected(self) -> None:
        with self.assertRaises(JsonToCsvError):
            unique_object([("id", 1), ("id", 2)])

    def test_duplicate_selected_fields_are_rejected(self) -> None:
        with self.assertRaises(JsonToCsvError):
            convert_rows([{"id": 1}], ["id", "id"])

    def test_empty_array_requires_explicit_field(self) -> None:
        with self.assertRaises(JsonToCsvError):
            convert_rows([])
        self.assertEqual(convert_rows([], ["id"]), (["id"], []))

    def test_writer_quotes_csv_values(self) -> None:
        output = io.StringIO()
        write_csv(output, ["id", "text"], [["1", "a,b"]], ",")
        self.assertEqual(output.getvalue(), 'id,text\n1,"a,b"\n')

    def test_cli_reads_stdin(self) -> None:
        source = json.dumps([{"id": 1, "active": True}, {"id": 2, "active": False}]).encode()
        result = self.run_cli(input_bytes=source)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"id,active\n1,true\n2,false\n")

    def test_cli_reads_file_and_selects_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "data.json")
            path.write_text('[{"id":1,"name":"A"}]', encoding="utf-8")
            result = self.run_cli(str(path), "--field", "name", "--field", "id")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"name,id\nA,1\n")

    def test_cli_supports_custom_delimiter(self) -> None:
        result = self.run_cli("--delimiter", ";", input_bytes=b'[{"id":1,"name":"A"}]')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"id;name\n1;A\n")

    def test_cli_rejects_nonstandard_number(self) -> None:
        result = self.run_cli(input_bytes=b'[{"value":NaN}]')
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"non-standard JSON number", result.stderr)

    def test_cli_rejects_overflowing_number(self) -> None:
        result = self.run_cli(input_bytes=b'[{"value":1e400}]')
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"is not finite", result.stderr)

    def test_cli_rejects_invalid_utf8(self) -> None:
        result = self.run_cli(input_bytes=b"\xff")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
