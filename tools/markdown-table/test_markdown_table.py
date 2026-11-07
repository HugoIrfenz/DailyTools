import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from markdown_table import TableError, format_markdown, split_row

SCRIPT = Path(__file__).with_name("markdown_table.py")

class MarkdownTableTests(unittest.TestCase):
    def test_aligns_basic_table(self):
        source = "| Name | Age |\n|---|---:|\n| Ada | 7 |\n| Grace Hopper | 85 |\n"
        expected = "| Name         | Age |\n| ------------ | ---: |\n| Ada          |   7 |\n| Grace Hopper |  85 |\n"
        self.assertEqual(format_markdown(source), expected)
    def test_table_without_outer_pipes(self):
        source = "Name | Value\n--- | ---\na | 1\n"
        self.assertEqual(format_markdown(source), "| Name | Value |\n| ---- | ----- |\n| a    | 1     |\n")
    def test_escaped_pipe_is_not_a_separator(self):
        self.assertEqual(split_row(r"| A\|B | C |"), [r"A\|B", "C"])
    def test_pipe_inside_inline_code_is_not_a_separator(self):
        self.assertEqual(split_row("| `a|b` | c |"), ["`a|b`", "c"])
    def test_multiple_backtick_delimiter(self):
        self.assertEqual(split_row("| ``a|`b`` | c |"), ["``a|`b``", "c"])
    def test_preserves_alignment(self):
        source = "| left | center | right |\n|:---|:---:|---:|\n| x | y | z |\n"
        output = format_markdown(source)
        self.assertIn("| :--- | :----: | ----: |", output)
        self.assertIn("| x    |   y    |     z |", output)
    def test_empty_cells(self):
        self.assertEqual(format_markdown("| A | B |\n|---|---|\n| | x |\n"), "| A | B |\n| --- | --- |\n|   | x |\n")
    def test_header_only_table(self):
        self.assertEqual(format_markdown("a|b\n---|---\n"), "| a | b |\n| --- | --- |\n")
    def test_multiple_tables_and_prose(self):
        source = "before\n\na|b\n---|---\nx|y\n\na longer|b\n---|---\n"
        result = format_markdown(source)
        self.assertTrue(result.startswith("before\n\n| a | b |"))
        self.assertIn("| a longer | b |", result)
    def test_non_table_text_is_unchanged(self):
        source = "# Heading\n\nA sentence with | a pipe.\n"
        self.assertEqual(format_markdown(source), source)
    def test_mismatched_row_width_is_reported(self):
        with self.assertRaisesRegex(TableError, "line 3: expected 2 columns, found 3"):
            format_markdown("a|b\n---|---\nx|y|z\n")
    def test_invalid_separator_is_not_treated_as_table(self):
        source = "a|b\n--|---\nx|y\n"
        self.assertEqual(format_markdown(source), source)
    def test_final_newline_is_preserved(self):
        self.assertTrue(format_markdown("a|b\n---|---\nx|y\n").endswith("\n"))
        self.assertFalse(format_markdown("a|b\n---|---\nx|y").endswith("\n"))
    def test_cli_stdin(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], input="a|bb\n---|---\nx|y\n", text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "| a | bb |\n| --- | --- |\n| x | y  |\n")
    def test_cli_reads_utf8_bom_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "table.md")
            path.write_bytes(b"\xef\xbb\xbfa|b\n---|---\nx|y\n")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("| a | b |", result.stdout)
    def test_cli_reports_column_mismatch(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], input="a|b\n---|---\nx|y|z\n", text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected 2 columns", result.stderr)

if __name__ == "__main__":
    unittest.main()
