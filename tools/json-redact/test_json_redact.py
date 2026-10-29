import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from json_redact import RedactError, decode_token, pointer_tokens, redact, replace_pointer, unique_object


SCRIPT = Path(__file__).with_name("json_redact.py")


class JsonRedactTests(unittest.TestCase):
    def run_cli(self, *args: str, input_bytes: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_replaces_object_value(self) -> None:
        value = replace_pointer({"auth": {"token": "secret"}}, "/auth/token", "x")
        self.assertEqual(value, {"auth": {"token": "x"}})

    def test_replaces_array_value(self) -> None:
        value = replace_pointer({"users": [{"email": "a"}]}, "/users/0/email", "x")
        self.assertEqual(value["users"][0]["email"], "x")

    def test_pointer_escapes_slash_and_tilde(self) -> None:
        self.assertEqual(pointer_tokens("/a~1b/~0key"), ["a/b", "~key"])
        value = replace_pointer({"a/b": {"~key": 1}}, "/a~1b/~0key", "x")
        self.assertEqual(value["a/b"]["~key"], "x")

    def test_empty_pointer_replaces_root(self) -> None:
        self.assertEqual(replace_pointer({"a": 1}, "", "x"), "x")

    def test_multiple_paths_are_replaced(self) -> None:
        value = redact({"a": 1, "b": 2}, ["/a", "/b"], "x", False)
        self.assertEqual(value, {"a": "x", "b": "x"})

    def test_missing_path_is_rejected(self) -> None:
        with self.assertRaises(RedactError):
            replace_pointer({"a": 1}, "/b", "x")

    def test_ignore_missing_continues(self) -> None:
        value = redact({"a": 1}, ["/missing", "/a"], "x", True)
        self.assertEqual(value, {"a": "x"})

    def test_ignore_missing_does_not_hide_invalid_pointer(self) -> None:
        with self.assertRaises(RedactError):
            redact({"a": 1}, ["invalid"], "x", True)

    def test_pointer_without_slash_is_rejected(self) -> None:
        with self.assertRaises(RedactError):
            pointer_tokens("a")

    def test_invalid_escape_is_rejected(self) -> None:
        with self.assertRaises(RedactError):
            decode_token("a~2b")

    def test_invalid_array_index_is_rejected(self) -> None:
        with self.assertRaises(RedactError):
            replace_pointer([1, 2], "/01", "x")

    def test_duplicate_object_keys_are_rejected(self) -> None:
        with self.assertRaises(RedactError):
            unique_object([("a", 1), ("a", 2)])

    def test_cli_reads_stdin_and_emits_unicode(self) -> None:
        source = json.dumps({"name": "Hugo", "secret": "rahasia"}).encode()
        result = self.run_cli("--path", "/secret", "--replacement", "tertutup", input_bytes=source)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"name": "Hugo", "secret": "tertutup"})

    def test_cli_compact_output(self) -> None:
        result = self.run_cli("--path", "/a", "--compact", input_bytes=b'{"a":1}')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'{"a":"[REDACTED]"}\n')

    def test_cli_reports_missing_path(self) -> None:
        result = self.run_cli("--path", "/b", input_bytes=b'{"a":1}')
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"path not found", result.stderr)

    def test_cli_rejects_duplicate_keys(self) -> None:
        result = self.run_cli("--path", "/a", input_bytes=b'{"a":1,"a":2}')
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"duplicate object key", result.stderr)

    def test_cli_rejects_invalid_utf8(self) -> None:
        result = self.run_cli("--path", "/a", input_bytes=b"\xff")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"error:", result.stderr)

    def test_cli_reads_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "data.json")
            path.write_text('{"token":"secret"}', encoding="utf-8")
            result = self.run_cli(str(path), "--path", "/token")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["token"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
