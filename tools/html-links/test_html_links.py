import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import html_links as tool


SCRIPT = Path(__file__).with_name("html_links.py")


class HtmlLinksTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )

    def test_extracts_supported_attributes_in_order(self):
        links = tool.extract('<a href="/a">A</a><img src="x.png"><form action="/go">', None, False)
        self.assertEqual([x["value"] for x in links], ["/a", "x.png", "/go"])

    def test_resolves_explicit_base(self):
        links = tool.extract('<a href="guide">x</a>', "https://example.test/docs/", False)
        self.assertEqual(links[0]["resolved"], "https://example.test/docs/guide")

    def test_document_base_is_used(self):
        links = tool.extract('<base href="https://e.test/app/"><a href="x">', None, False)
        self.assertEqual(links[0]["resolved"], "https://e.test/app/x")

    def test_explicit_base_overrides_document_base(self):
        links = tool.extract('<base href="https://wrong/"><a href="x">', "https://right/", False)
        self.assertEqual(links[0]["resolved"], "https://right/x")

    def test_first_document_base_wins(self):
        links = tool.extract('<base href="https://one/"><base href="https://two/"><a href="x">', None, False)
        self.assertEqual(links[0]["resolved"], "https://one/x")

    def test_unique_uses_resolved_value(self):
        links = tool.extract('<a href="x"><a href="./x">', "https://e.test/a/", True)
        self.assertEqual(len(links), 1)

    def test_non_unique_retains_duplicates(self):
        links = tool.extract('<a href="x"><a href="x">', None, False)
        self.assertEqual(len(links), 2)

    def test_empty_attributes_are_ignored(self):
        self.assertEqual(tool.extract('<a href=" "><img>', None, False), [])

    def test_character_references_are_decoded(self):
        links = tool.extract('<a href="/search?a=1&amp;b=2">', None, False)
        self.assertEqual(links[0]["value"], "/search?a=1&b=2")

    def test_self_closing_tag(self):
        links = tool.extract('<img src="a.png"/>', None, False)
        self.assertEqual(links[0]["tag"], "img")

    def test_comments_are_ignored(self):
        self.assertEqual(tool.extract('<!-- <a href="hidden"> -->', None, False), [])

    def test_cli_plain_output_from_stdin(self):
        result = self.run_cli("-", "--base", "https://e.test/", data=b'<a href="docs">')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"https://e.test/docs\n")

    def test_cli_json_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text('<script src="app.js"></script>', encoding="utf-8")
            result = self.run_cli(str(path), "--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)[0]["attribute"], "src")

    def test_cli_invalid_utf8(self):
        result = self.run_cli("-", data=b"\xff")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"not valid UTF-8", result.stderr)

    def test_cli_no_links_has_empty_output(self):
        result = self.run_cli("-", data=b"<p>none</p>")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")


if __name__ == "__main__":
    unittest.main()
