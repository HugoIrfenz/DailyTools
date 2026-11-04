import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import toml_inspect as tool


SCRIPT = Path(__file__).with_name("toml_inspect.py")


class TomlInspectTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def test_root_and_nested_table(self):
        result = tool.inspect_toml('title="x"\n[db]\nport=5432\n')
        self.assertEqual(result["table_count"], 2)
        self.assertEqual(result["tables"][0]["path"], [])
        self.assertEqual(result["tables"][1]["path"], ["db"])

    def test_values_are_not_reported(self):
        result = tool.inspect_toml('password="super-secret"\n')
        self.assertNotIn("super-secret", json.dumps(result))

    def test_scalar_types(self):
        result = tool.inspect_toml('s="x"\ni=1\nf=1.5\nb=true\n')
        kinds = {item["name"]: item["type"] for item in result["tables"][0]["keys"]}
        self.assertEqual(kinds, {"s": "string", "i": "integer", "f": "float", "b": "boolean"})

    def test_datetime_types(self):
        result = tool.inspect_toml('d=2026-11-04\nt=12:30:00\ndt=2026-11-04T12:30:00Z\n')
        kinds = {item["name"]: item["type"] for item in result["tables"][0]["keys"]}
        self.assertEqual(kinds, {"d": "date", "t": "time", "dt": "datetime"})

    def test_array_type_and_length(self):
        result = tool.inspect_toml('ports=[80,443]\n')
        key = result["tables"][0]["keys"][0]
        self.assertEqual(key["type"], "array<integer>")
        self.assertEqual(key["length"], 2)

    def test_empty_array(self):
        key = tool.inspect_toml('items=[]\n')["tables"][0]["keys"][0]
        self.assertEqual(key["type"], "array<empty>")

    def test_array_of_tables_creates_instance_tables(self):
        result = tool.inspect_toml('[[products]]\nname="a"\n[[products]]\nname="b"\n')
        paths = [table["path"] for table in result["tables"]]
        self.assertIn(["products", "0"], paths)
        self.assertIn(["products", "1"], paths)

    def test_dotted_table_path(self):
        result = tool.inspect_toml('[server.tls]\nenabled=true\n')
        self.assertIn(["server", "tls"], [table["path"] for table in result["tables"]])

    def test_source_order_is_preserved(self):
        result = tool.inspect_toml('z=1\na=2\n')
        self.assertEqual([x["name"] for x in result["tables"][0]["keys"]], ["z", "a"])

    def test_invalid_toml_is_rejected(self):
        with self.assertRaisesRegex(tool.InspectError, "invalid TOML"):
            tool.inspect_toml('a = [')

    def test_duplicate_key_is_rejected(self):
        with self.assertRaises(tool.InspectError):
            tool.inspect_toml('a=1\na=2\n')

    def test_empty_document(self):
        result = tool.inspect_toml('')
        self.assertEqual(result["table_count"], 1)
        self.assertEqual(result["value_key_count"], 0)

    def test_cli_reads_stdin_json(self):
        result = self.run_cli("-", data=b'[app]\nenabled=true\n')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["value_key_count"], 1)

    def test_cli_reads_bom_file_as_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_bytes(b'\xef\xbb\xbfname="x"\n')
            result = self.run_cli(str(path), "--text")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"name: string", result.stdout)

    def test_cli_invalid_utf8(self):
        result = self.run_cli("-", data=b"\xff\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)


if __name__ == "__main__":
    unittest.main()
