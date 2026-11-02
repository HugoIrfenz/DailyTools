import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import ini_inspect as tool


SCRIPT = Path(__file__).with_name("ini_inspect.py")


class IniInspectTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_lists_defaults_sections_and_explicit_keys(self):
        result = tool.inspect_ini(
            "[DEFAULT]\ntimeout=30\n[server]\nhost=localhost\nport=8080\n"
        )
        self.assertEqual(result["default_keys"], ["timeout"])
        self.assertEqual(result["sections"], [
            {"name": "server", "key_count": 2, "keys": ["host", "port"]}
        ])
        self.assertEqual(result["key_count"], 3)

    def test_source_order_is_preserved(self):
        result = tool.inspect_ini("[z]\nb=1\na=2\n[a]\nx=3\n")
        self.assertEqual([x["name"] for x in result["sections"]], ["z", "a"])
        self.assertEqual(result["sections"][0]["keys"], ["b", "a"])

    def test_key_case_is_preserved(self):
        result = tool.inspect_ini("[s]\nAPIKey=value\napikey=other\n")
        self.assertEqual(result["sections"][0]["keys"], ["APIKey", "apikey"])

    def test_colon_and_equals_delimiters(self):
        result = tool.inspect_ini("[s]\na: 1\nb = 2\n")
        self.assertEqual(result["sections"][0]["key_count"], 2)

    def test_no_value_option(self):
        result = tool.inspect_ini("[features]\nenabled\n")
        self.assertEqual(result["sections"][0]["keys"], ["enabled"])

    def test_percent_is_not_interpolated(self):
        result = tool.inspect_ini("[s]\npattern=%(missing)s\n")
        self.assertEqual(result["key_count"], 1)

    def test_comments_and_blank_lines_are_ignored(self):
        result = tool.inspect_ini("; comment\n# another\n\n[s]\nkey=value\n")
        self.assertEqual(result["section_count"], 1)

    def test_empty_input_is_valid(self):
        result = tool.inspect_ini("")
        self.assertEqual(result, {
            "section_count": 0, "key_count": 0, "default_keys": [], "sections": []
        })

    def test_duplicate_section_is_rejected_without_value(self):
        with self.assertRaisesRegex(tool.InspectError, "duplicate section 's'"):
            tool.inspect_ini("[s]\nsecret=first\n[s]\nsecret=second\n")

    def test_duplicate_option_is_rejected_without_value(self):
        with self.assertRaisesRegex(tool.InspectError, "duplicate option 'key'") as context:
            tool.inspect_ini("[s]\nkey=private-one\nkey=private-two\n")
        self.assertNotIn("private", str(context.exception))

    def test_missing_section_header_is_rejected_without_line_content(self):
        with self.assertRaises(tool.InspectError) as context:
            tool.inspect_ini("password=do-not-print\n")
        self.assertEqual(str(context.exception), "missing section header at line 1")

    def test_continuation_after_no_value_is_rejected(self):
        with self.assertRaisesRegex(tool.InspectError, "continuation after"):
            tool.inspect_ini("[s]\nflag\n  continuation\n")

    def test_render_text_has_names_not_values(self):
        result = tool.inspect_ini("[s]\nuser=alice\n")
        rendered = tool.render_text(result)
        self.assertIn("user", rendered)
        self.assertNotIn("alice", rendered)

    def test_cli_reads_stdin_as_json(self):
        result = self.run_cli("-", data=b"[app]\nmode=prod\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["sections"][0]["keys"], ["mode"])

    def test_cli_reads_bom_file_and_writes_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.ini"
            path.write_bytes(b"\xef\xbb\xbf[s]\nkey=value\n")
            result = self.run_cli(str(path), "--text")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"[s] (1)", result.stdout)

    def test_cli_rejects_invalid_utf8(self):
        result = self.run_cli("-", data=b"[s]\nkey=\xff\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)


if __name__ == "__main__":
    unittest.main()
