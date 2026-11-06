import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonl_dedupe import JsonlDedupeError, deduplicate, resolve_pointer


SCRIPT = Path(__file__).with_name("jsonl_dedupe.py")


class JsonlDedupeTests(unittest.TestCase):
    def test_semantic_object_duplicates(self):
        output, summary = deduplicate('{"a":1,"b":2}\n{"b":2,"a":1}\n', [])
        self.assertEqual(output, '{"a":1,"b":2}\n')
        self.assertEqual(summary["duplicates"], 1)

    def test_distinct_values_remain_in_order(self):
        output, summary = deduplicate("1\n2\n1\n3\n", [])
        self.assertEqual(output, "1\n2\n3\n")
        self.assertEqual(summary["unique"], 3)

    def test_key_pointer_deduplicates_different_objects(self):
        source = '{"id":1,"name":"first"}\n{"id":1,"name":"second"}\n'
        output, _ = deduplicate(source, ["/id"])
        self.assertEqual(output, '{"id":1,"name":"first"}\n')

    def test_composite_key(self):
        source = '{"team":"a","id":1,"v":"x"}\n{"team":"b","id":1,"v":"y"}\n{"team":"a","id":1,"v":"z"}\n'
        output, summary = deduplicate(source, ["/team", "/id"])
        self.assertEqual(len(output.splitlines()), 2)
        self.assertEqual(summary["duplicates"], 1)

    def test_keep_last_preserves_retained_record_order(self):
        source = '{"id":1,"v":"old"}\n{"id":2,"v":"same"}\n{"id":1,"v":"new"}\n'
        output, _ = deduplicate(source, ["/id"], "last")
        self.assertEqual(
            output,
            '{"id":2,"v":"same"}\n{"id":1,"v":"new"}\n',
        )

    def test_blank_lines_are_ignored(self):
        output, summary = deduplicate("\n1\n  \n1\n", [])
        self.assertEqual(output, "1\n")
        self.assertEqual(summary["records"], 2)

    def test_empty_input(self):
        output, summary = deduplicate("", [])
        self.assertEqual(output, "")
        self.assertEqual(summary["unique"], 0)

    def test_unicode_is_not_ascii_escaped(self):
        output, _ = deduplicate('{"name":"José"}\n', [])
        self.assertEqual(output, '{"name":"José"}\n')

    def test_array_pointer(self):
        self.assertEqual(resolve_pointer({"items": ["a", "b"]}, "/items/1"), "b")

    def test_escaped_pointer_tokens(self):
        value = {"a/b": {"~key": 7}}
        self.assertEqual(resolve_pointer(value, "/a~1b/~0key"), 7)

    def test_root_pointer(self):
        value = {"id": 1}
        self.assertIs(resolve_pointer(value, ""), value)

    def test_missing_pointer_reports_line(self):
        with self.assertRaisesRegex(JsonlDedupeError, "line 2.*does not exist"):
            deduplicate('{"id":1}\n{"name":"x"}\n', ["/id"])

    def test_invalid_pointer_escape(self):
        with self.assertRaisesRegex(JsonlDedupeError, "invalid JSON Pointer escape"):
            deduplicate('{"id":1}\n', ["/bad~2key"])

    def test_array_pointer_requires_index(self):
        with self.assertRaisesRegex(JsonlDedupeError, "array index"):
            deduplicate('{"items":[1]}\n', ["/items/x"])

    def test_invalid_json_reports_line(self):
        with self.assertRaisesRegex(JsonlDedupeError, "line 2: invalid JSON"):
            deduplicate('{"ok":1}\nnot-json\n', [])

    def test_non_standard_numbers_are_rejected(self):
        with self.assertRaisesRegex(JsonlDedupeError, "non-standard number"):
            deduplicate('{"value":NaN}\n', [])

    def test_repeated_key_pointer_is_rejected(self):
        with self.assertRaisesRegex(JsonlDedupeError, "must be unique"):
            deduplicate('{"id":1}\n', ["/id", "/id"])

    def test_cli_stdin_and_stats(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--key", "/id", "--stats"],
            input='{"id":1}\n{"id":1}\n',
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '{"id":1}\n')
        self.assertEqual(json.loads(result.stderr)["duplicates"], 1)

    def test_cli_check_exit_status(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            input="1\n1\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)

    def test_cli_reads_utf8_bom_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "records.jsonl")
            path.write_bytes(b"\xef\xbb\xbf{\"id\":1}\n{\"id\":1}\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '{"id":1}\n')

    def test_cli_reports_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "bad.jsonl")
            path.write_bytes(b"{\"id\":\xff}\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
