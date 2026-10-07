import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import duplicate_finder as tool


class DuplicateFinderTests(unittest.TestCase):
    def write(self, root, relative, content):
        path = Path(root) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_finds_duplicates_and_reclaimable_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, "a.txt", b"same")
            self.write(folder, "nested/b.txt", b"same")
            self.write(folder, "unique.txt", b"nope")
            groups, errors, hashed = tool.scan(folder)
            self.assertEqual(errors, [])
            self.assertEqual(groups[0]["files"], ["a.txt", "nested/b.txt"])
            self.assertEqual(groups[0]["reclaimable_bytes"], 4)
            self.assertEqual(hashed, 3)

    def test_same_size_different_content_is_not_duplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, "a", b"abc")
            self.write(folder, "b", b"xyz")
            groups, errors, hashed = tool.scan(folder)
            self.assertEqual((groups, errors, hashed), ([], [], 2))

    def test_min_size_and_empty_files(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, "empty-a", b"")
            self.write(folder, "empty-b", b"")
            self.write(folder, "tiny-a", b"x")
            self.write(folder, "tiny-b", b"x")
            self.assertEqual(tool.scan(folder, min_size=2)[0], [])
            groups, _, _ = tool.scan(folder, min_size=0)
            self.assertEqual([group["size"] for group in groups], [1, 0])

    def test_exclude_by_name_and_relative_glob(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, "keep/a.bin", b"same")
            self.write(folder, "cache/a.bin", b"same")
            self.write(folder, "keep/b.tmp", b"same")
            groups, errors, _ = tool.scan(folder, patterns=["cache", "*.tmp"])
            self.assertEqual(groups, [])
            self.assertEqual(errors, [])

    def test_symlinks_are_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            target = self.write(folder, "target", b"same")
            self.write(folder, "copy", b"same")
            link = Path(folder) / "link"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            groups, _, _ = tool.scan(folder)
            self.assertEqual(groups[0]["files"], ["copy", "target"])

    def test_hardlinks_are_not_counted_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            first = self.write(folder, "first", b"same")
            try:
                os.link(first, Path(folder) / "hardlink")
            except OSError:
                self.skipTest("hardlinks unavailable")
            groups, errors, hashed = tool.scan(folder)
            self.assertEqual((groups, errors, hashed), ([], [], 0))

    def test_invalid_roots(self):
        with tempfile.TemporaryDirectory() as folder:
            file_path = self.write(folder, "file", b"x")
            self.assertTrue(tool.scan(file_path)[1])
            self.assertTrue(tool.scan(Path(folder) / "missing")[1])

    def test_cli_json_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, "a", b"same")
            self.write(folder, "b", b"same")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(tool.main([folder, "--json"]), 1)
            report = json.loads(output.getvalue())
            self.assertEqual(report["duplicate_group_count"], 1)
            self.assertEqual(report["reclaimable_bytes"], 4)

    def test_clean_cli_and_bad_minimum(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, "only", b"unique")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tool.main([folder]), 0)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(tool.main([folder, "--min-size", "-1"]), 2)

    def test_human_bytes(self):
        self.assertEqual(tool.human_bytes(0), "0 B")
        self.assertEqual(tool.human_bytes(1024), "1.0 KiB")
        self.assertEqual(tool.human_bytes(1024 * 1024 + 512 * 1024), "1.5 MiB")


if __name__ == "__main__":
    unittest.main()
