import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import path_collisions as tool

SCRIPT = Path(__file__).with_name("path_collisions.py")


class PathCollisionsTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def test_ascii_case_collision_and_clean_paths(self):
        report = tool.find_collisions(["README.md", "readme.md", "src/code.py"])
        self.assertEqual(report["groups"], [["README.md", "readme.md"]])
        self.assertEqual(report["colliding_path_count"], 2)
        self.assertFalse(report["ok"])
        self.assertTrue(tool.find_collisions(["a", "b"])["ok"])

    def test_unicode_composed_and_decomposed_names(self):
        names = ["caf\u00e9.txt", "cafe\u0301.txt"]
        report = tool.find_collisions(names, case_sensitive=True)
        self.assertEqual(report["collision_group_count"], 1)
        self.assertEqual(report["groups"], [sorted(names)])

    def test_unicode_casefold_and_normalization(self):
        self.assertEqual(tool.comparison_key("Straße"), tool.comparison_key("STRASSE"))
        self.assertEqual(tool.comparison_key("Å"), tool.comparison_key("a\u030a"))

    def test_case_sensitive_disables_only_casefold(self):
        report = tool.find_collisions(["A", "a", "é", "e\u0301"], case_sensitive=True)
        self.assertEqual(report["groups"], [["e\u0301", "é"]])

    def test_parent_directory_keys_are_compared_too(self):
        report = tool.find_collisions(["Src", "src", "Src/API.py", "src/api.py"])
        self.assertEqual(report["collision_group_count"], 2)
        self.assertEqual(report["entry_count"], 4)

    def test_display_limit_and_zero_still_count_everything(self):
        paths = [f"{case}{i}" for i in range(30) for case in ("A", "a")]
        report = tool.find_collisions(iter(paths), max_groups=2)
        self.assertEqual(report["collision_group_count"], 30)
        self.assertEqual(report["omitted_group_count"], 28)
        self.assertEqual(len(report["groups"]), 2)
        zero = tool.find_collisions(paths, max_groups=0)
        self.assertEqual(zero["groups"], [])
        self.assertFalse(zero["ok"])

    def test_output_order_is_independent_of_traversal(self):
        paths = ["b", "B", "a", "A"]
        self.assertEqual(tool.find_collisions(paths), tool.find_collisions(reversed(paths)))

    def test_empty_directory_and_nested_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(list(tool.scan_paths(root)), [])
            (root / "sub").mkdir()
            (root / "sub" / "file").write_bytes(b"data")
            (root / ".hidden").write_bytes(b"")
            self.assertEqual(set(tool.scan_paths(root)), {"sub", "sub/file", ".hidden"})

    def test_symlink_name_included_but_target_not_traversed(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "root"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "not-scanned").write_bytes(b"private")
            (root / "link").symlink_to(outside, target_is_directory=True)
            self.assertEqual(list(tool.scan_paths(root)), ["link"])
            result = self.cli(root / "link")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")

    def test_cli_real_collision_reports_json_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "Config").write_bytes(b"one")
            (root / "config").write_bytes(b"two")
            result = self.cli(root, "--json")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["groups"], [["Config", "config"]])
            self.assertEqual((root / "Config").read_bytes(), b"one")
            self.assertEqual((root / "config").read_bytes(), b"two")
            self.assertEqual(self.cli(root, "--case-sensitive").returncode, 0)

    def test_cli_paths_are_escaped_for_text_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "A\nfile").touch()
            (root / "a\nfile").touch()
            result = self.cli(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn('"A\\nfile"', result.stdout)
            self.assertNotIn("A\nfile", result.stdout)

    def test_scan_error_yields_no_partial_report(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(tool.os, "scandir", side_effect=PermissionError):
                with patch("sys.stderr"), patch("sys.stdout") as stdout:
                    self.assertEqual(tool.main([folder]), 2)
                    stdout.write.assert_not_called()

    def test_missing_root_file_root_and_invalid_option(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / "file"
            file.write_text("x")
            for args in ((root / "missing",), (file,), (root, "--max-groups", "-1"),
                         (root, "--max-groups", "bad")):
                with self.subTest(args=args):
                    result = self.cli(*args)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
