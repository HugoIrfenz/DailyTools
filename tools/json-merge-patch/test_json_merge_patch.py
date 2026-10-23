import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from json_merge_patch import MergePatchError, load_json, merge_patch


SCRIPT = Path(__file__).with_name("json_merge_patch.py")


class JSONMergePatchTests(unittest.TestCase):
    def test_updates_adds_and_removes_members(self):
        target = {"name": "Ada", "active": True, "old": 1}
        patch = {"active": False, "role": "admin", "old": None}
        self.assertEqual(
            merge_patch(target, patch),
            {"name": "Ada", "active": False, "role": "admin"},
        )

    def test_merges_nested_objects(self):
        target = {"profile": {"name": "Ada", "city": "London"}}
        patch = {"profile": {"city": "Paris"}}
        self.assertEqual(
            merge_patch(target, patch),
            {"profile": {"name": "Ada", "city": "Paris"}},
        )

    def test_array_is_replaced(self):
        self.assertEqual(merge_patch({"items": [1, 2]}, {"items": [3]}), {"items": [3]})

    def test_scalar_patch_replaces_whole_target(self):
        self.assertEqual(merge_patch({"a": 1}, "replacement"), "replacement")

    def test_null_patch_replaces_whole_target(self):
        self.assertIsNone(merge_patch({"a": 1}, None))

    def test_object_patch_converts_scalar_target(self):
        self.assertEqual(merge_patch(5, {"a": 1}), {"a": 1})

    def test_missing_null_member_is_ignored(self):
        self.assertEqual(merge_patch({"a": 1}, {"missing": None}), {"a": 1})

    def test_inputs_are_not_mutated(self):
        target = {"a": {"b": 1}}
        patch = {"a": {"c": 2}}
        merge_patch(target, patch)
        self.assertEqual(target, {"a": {"b": 1}})
        self.assertEqual(patch, {"a": {"c": 2}})

    def test_duplicate_keys_are_rejected(self):
        with self.assertRaisesRegex(MergePatchError, "duplicate object key"):
            load_json(io.StringIO('{"a":1,"a":2}'), "input")

    def test_nonstandard_numbers_are_rejected(self):
        with self.assertRaisesRegex(MergePatchError, "non-standard"):
            load_json(io.StringIO('{"a":NaN}'), "input")

    def test_invalid_json_names_source(self):
        with self.assertRaisesRegex(MergePatchError, "target.json"):
            load_json(io.StringIO("{"), "target.json")

    def test_cli_applies_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            patch = root / "patch.json"
            target.write_text('{"a":1,"b":2}', encoding="utf-8")
            patch.write_text('{"b":null,"c":3}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(target), str(patch), "--compact"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"a": 1, "c": 3})

    def test_cli_rejects_stdin_patch(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "target.json", "-"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("stdin is reserved", result.stderr)


if __name__ == "__main__":
    unittest.main()
