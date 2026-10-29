import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from markdown_link_check import extract_targets, local_path, run_check


SCRIPT = Path(__file__).with_name("markdown_link_check.py")


class MarkdownLinkCheckTests(unittest.TestCase):
    def run_cli(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=stdin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_extracts_inline_image_and_reference_targets(self) -> None:
        text = "[doc](docs/a.md)\n![image](img/a.png)\n[id]: other.md\n"
        self.assertEqual(
            extract_targets(text),
            [(1, "docs/a.md"), (2, "img/a.png"), (3, "other.md")],
        )

    def test_ignores_fenced_and_inline_code(self) -> None:
        text = "`[x](missing.md)`\n```md\n[x](also.md)\n```\n[ok](real.md)"
        self.assertEqual(extract_targets(text), [(5, "real.md")])

    def test_external_anchor_and_root_links_are_not_local_files(self) -> None:
        self.assertIsNone(local_path("https://example.com/a"))
        self.assertIsNone(local_path("#section"))
        self.assertIsNone(local_path("/site/path"))

    def test_malformed_external_url_is_skipped(self) -> None:
        self.assertIsNone(local_path("http://[broken"))

    def test_query_and_fragment_are_removed_from_path(self) -> None:
        self.assertEqual(local_path("doc.md?raw=1#part"), "doc.md")

    def test_percent_encoded_path_is_decoded(self) -> None:
        self.assertEqual(local_path("my%20file.md"), "my file.md")

    def test_existing_relative_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "target.md").write_text("ok", encoding="utf-8")
            source = root / "README.md"
            source.write_text("[target](target.md)", encoding="utf-8")
            result = run_check(source)
        self.assertEqual(result["local_links"], 1)
        self.assertEqual(result["missing"], [])

    def test_missing_file_reports_line_and_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "README.md")
            source.write_text("title\n[missing](no.md)", encoding="utf-8")
            result = run_check(source)
        self.assertEqual(result["missing"][0]["line"], 2)
        self.assertEqual(result["missing"][0]["target"], "no.md")

    def test_directory_scan_is_recursive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sub").mkdir()
            (root / "README.md").write_text("[sub](sub/doc.md)", encoding="utf-8")
            (root / "sub" / "doc.md").write_text("[root](../README.md)", encoding="utf-8")
            result = run_check(root)
        self.assertEqual(result["files"], 2)
        self.assertEqual(result["local_links"], 2)
        self.assertEqual(result["missing"], [])

    def test_stdin_uses_base_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "target.txt").write_text("ok", encoding="utf-8")
            result = run_check(Path("-"), "[x](target.txt)", root)
        self.assertEqual(result["missing"], [])

    def test_cli_returns_one_for_missing_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "README.md")
            source.write_text("[x](missing.md)", encoding="utf-8")
            result = self.run_cli(str(source))
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing missing.md", result.stdout)

    def test_cli_json_for_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "README.md")
            source.write_text("[section](#part)", encoding="utf-8")
            result = self.run_cli(str(source), "--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["local_links"], 0)

    def test_cli_reports_missing_input(self) -> None:
        result = self.run_cli("does-not-exist.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_cli_rejects_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "README.md")
            source.write_bytes(b"\xff")
            result = self.run_cli(str(source))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
