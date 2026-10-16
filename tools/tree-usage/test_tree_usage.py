import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import tree_usage as tool

SCRIPT = Path(__file__).with_name("tree_usage.py")


class TreeUsageTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def test_nested_counts_and_casefold_extensions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "sub").mkdir()
            (root / "a.TXT").write_bytes(b"123")
            (root / "sub" / "b.txt").write_bytes(b"45")
            result = tool.summarize(root)
            self.assertEqual(result["file_count"], 2)
            self.assertEqual(result["total_bytes"], 5)
            self.assertEqual(result["groups"], [{"extension": ".txt", "file_count": 2, "bytes": 5}])

    def test_hidden_no_extension_and_final_suffix(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in (".env", "README", "archive.tar.gz"):
                (root / name).write_bytes(b"x")
            result = tool.summarize(root)
            groups = {g["extension"]: g["file_count"] for g in result["groups"]}
            self.assertEqual(groups, {"": 2, ".gz": 1})

    def test_empty_tree_and_zero_byte_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(tool.summarize(root)["groups"], [])
            (root / "empty.log").touch()
            result = tool.summarize(root)
            self.assertEqual(result["file_count"], 1)
            self.assertEqual(result["total_bytes"], 0)

    def test_top_limit_retains_totals_and_tie_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("a.z", "a.a", "a.b"):
                (root / name).write_bytes(b"x")
            result = tool.summarize(root, top=1)
            self.assertEqual(result["groups"][0]["extension"], ".a")
            self.assertEqual(result["total_bytes"], 3)
            self.assertEqual(result["omitted_group_count"], 2)
            self.assertEqual(tool.summarize(root, top=0)["groups"], [])

    def test_largest_group_first(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.small").write_bytes(b"x")
            (root / "b.large").write_bytes(b"12345")
            self.assertEqual(tool.summarize(root)["groups"][0]["extension"], ".large")

    def test_symlinks_and_dangling_links_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "root"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "large").write_bytes(b"x" * 1000)
            (root / "dirlink").symlink_to(outside, target_is_directory=True)
            (root / "dead").symlink_to(base / "missing")
            result = tool.summarize(root)
            self.assertEqual(result["file_count"], 0)
            self.assertEqual(result["skipped_symlink_count"], 2)
            self.assertEqual(self.cli(root / "dirlink").returncode, 2)

    def test_hardlinks_count_per_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = root / "a.bin"
            first.write_bytes(b"abc")
            os.link(first, root / "b.bin")
            self.assertEqual(tool.summarize(root)["total_bytes"], 6)

    def test_fifo_is_special_not_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            os.mkfifo(root / "pipe")
            result = tool.summarize(root)
            self.assertEqual(result["skipped_special_count"], 1)
            self.assertEqual(result["file_count"], 0)

    def test_cli_json_text_and_unchanged_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / "a.txt"
            file.write_bytes(b"abc")
            result = self.cli(root, "--json")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["total_bytes"], 3)
            self.assertIn("logical bytes: 3", self.cli(root).stdout)
            self.assertEqual(file.read_bytes(), b"abc")

    def test_cli_errors_and_no_partial_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for args in ((root / "missing",), (root, "--top", "-1"), (root, "--top", "bad")):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
            with patch.object(tool.os, "scandir", side_effect=PermissionError):
                with patch("sys.stderr"), patch("sys.stdout") as stdout:
                    self.assertEqual(tool.main([str(root)]), 2)
                    stdout.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
