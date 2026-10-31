import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from xml_stats import XmlStatsError, namespace_uri, render_text, summarize_xml


SCRIPT = Path(__file__).with_name("xml_stats.py")


class XmlStatsTests(unittest.TestCase):
    def run_cli(self, *args: str, input_bytes: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_counts_elements_attributes_depth_and_tags(self) -> None:
        summary = summarize_xml(b'<root a="1"><item/><group><item b="2"/></group></root>')
        self.assertEqual(summary["elements"], 4)
        self.assertEqual(summary["attributes"], 2)
        self.assertEqual(summary["max_depth"], 3)
        self.assertEqual(summary["tags"], [
            {"name": "group", "count": 1},
            {"name": "item", "count": 2},
            {"name": "root", "count": 1},
        ])

    def test_counts_text_and_tail_characters(self) -> None:
        summary = summarize_xml(b"<root>Hello<child>world</child>!</root>")
        self.assertEqual(summary["text_characters"], 11)

    def test_reports_element_and_attribute_namespaces(self) -> None:
        data = b'<r xmlns="urn:main" xmlns:x="urn:x" x:id="1"><x:c/></r>'
        summary = summarize_xml(data)
        self.assertEqual(summary["root"], "{urn:main}r")
        self.assertEqual(summary["namespaces"], ["urn:main", "urn:x"])

    def test_namespace_uri_for_plain_and_expanded_names(self) -> None:
        self.assertIsNone(namespace_uri("root"))
        self.assertEqual(namespace_uri("{urn:test}root"), "urn:test")

    def test_self_closing_root_has_depth_one(self) -> None:
        summary = summarize_xml(b"<root/>")
        self.assertEqual(summary["elements"], 1)
        self.assertEqual(summary["max_depth"], 1)

    def test_comments_and_processing_instructions_are_not_elements(self) -> None:
        summary = summarize_xml(b"<?xml version='1.0'?><root><!-- note --><?go now?></root>")
        self.assertEqual(summary["elements"], 1)

    def test_escaped_entities_count_as_decoded_text(self) -> None:
        summary = summarize_xml(b"<root>&lt;&amp;&gt;</root>")
        self.assertEqual(summary["text_characters"], 3)

    def test_doctype_is_rejected(self) -> None:
        with self.assertRaises(XmlStatsError):
            summarize_xml(b"<!DOCTYPE root><root/>")

    def test_malformed_xml_is_rejected(self) -> None:
        with self.assertRaises(Exception):
            summarize_xml(b"<root><x></root>")

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaises(Exception):
            summarize_xml(b"")

    def test_text_render_contains_summary(self) -> None:
        rendered = render_text(summarize_xml(b"<root><item/></root>"))
        self.assertIn("elements: 2", rendered)
        self.assertIn("max depth: 2", rendered)

    def test_cli_reads_stdin_as_json(self) -> None:
        result = self.run_cli("--json", input_bytes=b"<root><item/></root>")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["elements"], 2)

    def test_cli_reads_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.xml")
            path.write_text("<root><item/></root>", encoding="utf-8")
            result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"root: root", result.stdout)

    def test_cli_reports_missing_file(self) -> None:
        result = self.run_cli("missing.xml")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"error:", result.stderr)

    def test_cli_rejects_invalid_xml_bytes(self) -> None:
        result = self.run_cli(input_bytes=b"<root>\xff</root>")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
