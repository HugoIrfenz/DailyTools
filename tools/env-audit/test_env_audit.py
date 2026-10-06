import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import env_audit as tool


class EnvAuditTests(unittest.TestCase):
    def write(self, folder, name, content):
        path = Path(folder) / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_matching_files_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            example = self.write(folder, ".env.example", "A=placeholder\nB=x\n")
            env = self.write(folder, ".env", "export A=secret\nB=2\n")
            self.assertEqual(tool.audit(example, env)[0], [])

    def test_missing_extra_empty_and_stable_order(self):
        with tempfile.TemporaryDirectory() as folder:
            example = self.write(folder, "example", "Z=x\nA=x\nEMPTY=x\n")
            env = self.write(folder, "env", "EXTRA=1\nEMPTY= # optional?\n")
            issues, _, _ = tool.audit(example, env)
            self.assertEqual([(i["code"], i.get("key")) for i in issues], [
                ("missing_key", "A"), ("missing_key", "Z"),
                ("unexpected_key", "EXTRA"), ("empty_value", "EMPTY")])

    def test_empty_forms_and_allow_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            example = self.write(folder, "example", "A=x\nB=x\nC=x\n")
            env = self.write(folder, "env", "A=\nB=''\nC=\"\"\n")
            issues, _, _ = tool.audit(example, env, allowed_empty=["A", "B", "C"])
            self.assertEqual(issues, [])

    def test_quoted_hash_is_not_empty(self):
        self.assertFalse(tool.is_empty("'#value'"))
        self.assertTrue(tool.is_empty(" # comment"))

    def test_duplicates_never_show_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, "env", "TOKEN=top-secret\nTOKEN=other-secret\n")
            _, issues = tool.parse_dotenv(path)
            rendered = json.dumps(issues)
            self.assertEqual(issues[0]["code"], "duplicate_key")
            self.assertNotIn("top-secret", rendered)
            self.assertNotIn("other-secret", rendered)

    def test_invalid_lines_and_names(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, "env", "NO_ASSIGNMENT\nBAD-NAME=x\n1BAD=y\n")
            _, issues = tool.parse_dotenv(path)
            self.assertEqual([i["code"] for i in issues],
                             ["invalid_line", "invalid_key", "invalid_key"])

    def test_comments_blank_lines_bom_and_unicode_value(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, "env", "\ufeff# comment\n\nNAME=猫\n")
            keys, issues = tool.parse_dotenv(path)
            self.assertEqual(set(keys), {"NAME"})
            self.assertEqual(issues, [])

    def test_cli_json_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            example = self.write(folder, "example", "A=x\n")
            env = self.write(folder, "env", "A=\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(tool.main([str(example), str(env), "--json"]), 1)
            report = json.loads(output.getvalue())
            self.assertFalse(report["ok"])
            self.assertEqual(set(report["issues"][0]),
                             {"code", "file", "line", "key", "message"})
            self.assertNotIn("before", report["issues"][0])
            self.assertNotIn("after", report["issues"][0])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tool.main([str(example), str(env), "--allow-empty", "A"]), 0)

    def test_allow_extra(self):
        with tempfile.TemporaryDirectory() as folder:
            example = self.write(folder, "example", "A=x\n")
            env = self.write(folder, "env", "A=1\nLOCAL_ONLY=1\n")
            self.assertEqual(tool.audit(example, env, allow_extra=True)[0], [])

    def test_missing_file_and_invalid_option_are_errors(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(tool.main(["missing", "also-missing"]), 2)
            self.assertEqual(tool.main(["missing", "also-missing", "--allow-empty", "BAD-X"]), 2)


if __name__ == "__main__":
    unittest.main()
