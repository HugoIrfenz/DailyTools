import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

from json_stats import JSONStatsError, collect_stats, format_text, load_json, type_name


SCRIPT = Path(__file__).with_name("json_stats.py")


class JSONStatsTests(unittest.TestCase):
    def test_counts_nested_document(self):
        stats = collect_stats({"users": [{"name": "Ada", "active": True}], "count": 1, "next": None})
        self.assertEqual(stats["root_type"], "object")
        self.assertEqual(stats["nodes"], 7)
        self.assertEqual(stats["max_depth"], 3)
        self.assertEqual(stats["type_counts"], {"object": 2, "array": 1, "string": 1, "number": 1, "boolean": 1, "null": 1})

    def test_counts_members_and_items(self):
        stats = collect_stats({"a": [1, 2], "b": {"c": 3, "d": 4, "e": 5}})
        self.assertEqual(stats["object_members"], 5)
        self.assertEqual(stats["array_items"], 2)
        self.assertEqual(stats["max_object_members"], 3)
        self.assertEqual(stats["max_array_items"], 2)

    def test_empty_containers_are_nodes(self):
        stats = collect_stats({"a": [], "b": {}})
        self.assertEqual(stats["nodes"], 3)
        self.assertEqual(stats["type_counts"]["array"], 1)
        self.assertEqual(stats["type_counts"]["object"], 2)

    def test_root_scalar_depth_is_zero(self):
        stats = collect_stats("hello")
        self.assertEqual((stats["root_type"], stats["max_depth"], stats["nodes"]), ("string", 0, 1))

    def test_boolean_is_not_counted_as_number(self):
        stats = collect_stats([True, 1])
        self.assertEqual(stats["type_counts"]["boolean"], 1)
        self.assertEqual(stats["type_counts"]["number"], 1)

    def test_type_name_all_json_types(self):
        values = [{}, [], "", 1, False, None]
        self.assertEqual([type_name(value) for value in values], ["object", "array", "string", "number", "boolean", "null"])

    def test_handles_deep_structure_iteratively(self):
        value = 0
        for _ in range(1500):
            value = [value]
        self.assertEqual(collect_stats(value)["max_depth"], 1500)

    def test_duplicate_keys_are_rejected(self):
        with self.assertRaisesRegex(JSONStatsError, "duplicate object key"):
            load_json(io.StringIO('{"a":1,"a":2}'), "input")

    def test_nonstandard_numbers_are_rejected(self):
        with self.assertRaisesRegex(JSONStatsError, "non-standard"):
            load_json(io.StringIO("Infinity"), "input")

    def test_invalid_json_names_source(self):
        with self.assertRaisesRegex(JSONStatsError, "data.json"):
            load_json(io.StringIO("{"), "data.json")

    def test_text_format_has_summary(self):
        text = format_text(collect_stats([1, 2]))
        self.assertIn("Root type: array", text)
        self.assertIn("Nodes: 3", text)

    def test_cli_json_from_stdin(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "-", "--json"], input='{"a":[1]}', text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["nodes"], 3)

    def test_cli_rejects_invalid_input(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "-"], input="{", text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
