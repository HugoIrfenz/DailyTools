import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import url_inspect as tool


SCRIPT = Path(__file__).with_name("url_inspect.py")


class UrlInspectTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def test_absolute_url(self):
        item = tool.inspect_url("https://example.com:8443/a/b?x=1&y=#frag", 1)
        self.assertEqual(item["scheme"], "https")
        self.assertEqual(item["host"], "example.com")
        self.assertEqual(item["port"], 8443)
        self.assertEqual(item["query_parameter_count"], 2)

    def test_relative_url(self):
        item = tool.inspect_url("../docs/readme", 1)
        self.assertFalse(item["has_authority"])
        self.assertEqual(item["path_segment_count"], 3)

    def test_unicode_host_has_idna_form(self):
        item = tool.inspect_url("https://münchen.example/path", 1)
        self.assertEqual(item["ascii_host"], "xn--mnchen-3ya.example")

    def test_ipv4_host(self):
        item = tool.inspect_url("http://127.0.0.1/", 1)
        self.assertEqual(item["host_kind"], "ip")

    def test_ipv6_host(self):
        item = tool.inspect_url("http://[2001:db8::1]:8080/", 1)
        self.assertEqual(item["host_kind"], "ip")
        self.assertEqual(item["port"], 8080)

    def test_credentials_are_only_reported_as_presence(self):
        item = tool.inspect_url("https://alice:secret@example.com/", 1)
        encoded = json.dumps(item)
        self.assertTrue(item["username_present"])
        self.assertTrue(item["password_present"])
        self.assertNotIn("alice", encoded)
        self.assertNotIn("secret", encoded)

    def test_fragment_value_is_not_reported(self):
        item = tool.inspect_url("https://example.com/#private", 1)
        self.assertTrue(item["fragment_present"])
        self.assertNotIn("private", json.dumps(item))

    def test_query_values_are_not_reported(self):
        item = tool.inspect_url("https://example.com/?token=secret", 1)
        self.assertEqual(item["query_parameter_count"], 1)
        self.assertNotIn("secret", json.dumps(item))

    def test_invalid_port_is_rejected(self):
        with self.assertRaisesRegex(tool.UrlError, "line 4"):
            tool.inspect_url("https://example.com:nope/", 4)

    def test_unmatched_ipv6_bracket_is_rejected(self):
        with self.assertRaises(tool.UrlError):
            tool.inspect_url("http://[2001:db8::1/", 1)

    def test_whitespace_is_rejected(self):
        with self.assertRaisesRegex(tool.UrlError, "whitespace"):
            tool.inspect_url("https://example.com/a b", 1)

    def test_surrounding_whitespace_is_rejected(self):
        with self.assertRaisesRegex(tool.UrlError, "whitespace"):
            tool.inspect_lines(" https://example.com\n")

    def test_blank_lines_are_ignored_and_line_numbers_preserved(self):
        result = tool.inspect_lines("\nhttps://example.com\n\n/docs\n")
        self.assertEqual([item["line"] for item in result], [2, 4])

    def test_cli_reads_stdin(self):
        result = self.run_cli("-", data=b"https://example.com/a\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)[0]["host"], "example.com")

    def test_cli_reads_bom_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "urls.txt"
            path.write_bytes(b"\xef\xbb\xbf/docs\n")
            result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)[0]["path"], "/docs")

    def test_cli_invalid_utf8(self):
        result = self.run_cli("-", data=b"\xff\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)


if __name__ == "__main__":
    unittest.main()
