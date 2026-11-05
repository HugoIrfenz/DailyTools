import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from markdown_toc import build_toc, iter_headings, slugify


SCRIPT = Path(__file__).with_name("markdown_toc.py")


class MarkdownTocTests(unittest.TestCase):
    def test_default_levels_skip_h1(self):
        source = "# Document\n\n## Start\n\n### Details\n"
        self.assertEqual(
            build_toc(source),
            "- [Start](#start)\n  - [Details](#details)",
        )

    def test_custom_levels(self):
        source = "# One\n## Two\n### Three\n"
        self.assertEqual(build_toc(source, 1, 2), "- [One](#one)\n  - [Two](#two)")

    def test_heading_level_gap_controls_indentation(self):
        self.assertEqual(build_toc("## Two\n#### Four\n"), "- [Two](#two)\n    - [Four](#four)")

    def test_closing_hashes_are_removed(self):
        self.assertEqual(build_toc("## Install ##   \n"), "- [Install](#install)")

    def test_hash_without_separating_space_is_content(self):
        self.assertEqual(build_toc("## C#\n"), "- [C#](#c)")

    def test_backtick_fence_is_ignored(self):
        source = "## Before\n```md\n## Hidden\n```\n## After\n"
        self.assertEqual(build_toc(source), "- [Before](#before)\n- [After](#after)")

    def test_tilde_fence_is_ignored(self):
        source = "~~~\n## Hidden\n~~~\n## Visible\n"
        self.assertEqual(build_toc(source), "- [Visible](#visible)")

    def test_short_fence_does_not_close_long_fence(self):
        source = "````\n```\n## Hidden\n````\n## Visible\n"
        self.assertEqual(build_toc(source), "- [Visible](#visible)")

    def test_inline_backticks_do_not_open_fence(self):
        self.assertEqual(build_toc("## Use `code` here\n"), "- [Use `code` here](#use-code-here)")

    def test_duplicate_anchors_receive_suffixes(self):
        source = "## Setup\n## Setup\n## SETUP\n"
        self.assertEqual(
            build_toc(source),
            "- [Setup](#setup)\n- [Setup](#setup-1)\n- [SETUP](#setup-2)",
        )

    def test_slug_rules(self):
        self.assertEqual(slugify("API: Foo & Bar!"), "api-foo-bar")
        self.assertEqual(slugify("Crème brûlée"), "crème-brûlée")
        self.assertEqual(slugify("a---b"), "a-b")

    def test_label_brackets_are_escaped(self):
        self.assertEqual(build_toc("## Parse [JSON]\n"), "- [Parse \\[JSON\\]](#parse-json)")

    def test_empty_or_punctuation_only_heading_is_skipped(self):
        self.assertEqual(build_toc("##\n## !!!\n## Kept\n"), "- [Kept](#kept)")

    def test_iter_headings_accepts_three_leading_spaces(self):
        self.assertEqual(list(iter_headings(["   ## Indented\n"])), [(2, "Indented")])

    def test_invalid_level_range_raises(self):
        with self.assertRaises(ValueError):
            build_toc("## Heading", 4, 2)

    def test_cli_reads_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--min-level", "1"],
            input="# Title\n## Child\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "- [Title](#title)\n  - [Child](#child)\n")
        self.assertEqual(result.stderr, "")

    def test_cli_reads_utf8_bom_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "README.md")
            path.write_bytes(b"\xef\xbb\xbf## Caf\xc3\xa9\r\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "- [Café](#café)\n")

    def test_cli_reports_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "bad.md")
            path.write_bytes(b"## \xff\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("error:", result.stderr)

    def test_cli_rejects_reversed_level_range(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--min-level", "5", "--max-level", "2"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot be greater", result.stderr)


if __name__ == "__main__":
    unittest.main()
