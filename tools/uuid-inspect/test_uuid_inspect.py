import json
import subprocess
import sys
import unittest
from pathlib import Path

from uuid_inspect import UUIDInspectError, format_text, inspect_uuid, parse_values


SCRIPT = Path(__file__).with_name("uuid_inspect.py")
V4 = "550e8400-e29b-41d4-a716-446655440000"


class UUIDInspectTests(unittest.TestCase):
    def test_inspects_version_4_uuid(self):
        item = inspect_uuid(V4)
        self.assertEqual(item["canonical"], V4)
        self.assertEqual(item["version"], 4)
        self.assertEqual(item["variant"], "rfc4122")
        self.assertFalse(item["is_nil"])

    def test_normalizes_uppercase_and_braces(self):
        item = inspect_uuid("{550E8400-E29B-41D4-A716-446655440000}")
        self.assertEqual(item["canonical"], V4)

    def test_accepts_compact_hex(self):
        item = inspect_uuid("550e8400e29b41d4a716446655440000")
        self.assertEqual(item["canonical"], V4)

    def test_nil_uuid(self):
        item = inspect_uuid("00000000-0000-0000-0000-000000000000")
        self.assertTrue(item["is_nil"])
        self.assertIsNone(item["version"])
        self.assertEqual(item["variant"], "ncs")

    def test_max_uuid(self):
        item = inspect_uuid("ffffffff-ffff-ffff-ffff-ffffffffffff")
        self.assertTrue(item["is_max"])
        self.assertEqual(item["variant"], "future")

    def test_invalid_uuid_is_rejected(self):
        with self.assertRaisesRegex(UUIDInspectError, "invalid UUID"):
            inspect_uuid("not-a-uuid")

    def test_empty_uuid_is_rejected(self):
        with self.assertRaisesRegex(UUIDInspectError, "empty"):
            inspect_uuid("  ")

    def test_parse_values_prefers_arguments(self):
        self.assertEqual(parse_values([V4], "ignored"), [V4])

    def test_parse_values_reads_nonempty_lines(self):
        self.assertEqual(parse_values([], f"\n{V4}\n\n"), [V4])

    def test_parse_values_rejects_empty_stdin(self):
        with self.assertRaisesRegex(UUIDInspectError, "provide"):
            parse_values([], "\n")

    def test_text_format_has_core_fields(self):
        output = format_text(inspect_uuid(V4))
        self.assertIn(f"UUID: {V4}", output)
        self.assertIn("Version: 4", output)
        self.assertIn("Variant: rfc4122", output)

    def test_cli_json_from_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            input=V4 + "\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)[0]["canonical"], V4)

    def test_cli_required_version_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), V4, "--require-version", "4"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_cli_required_version_fails(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), V4, "--require-version", "1"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("do not have version 1", result.stderr)


if __name__ == "__main__":
    unittest.main()
