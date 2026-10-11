import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import hash_manifest as tool


SCRIPT = Path(__file__).with_name("hash_manifest.py")


class HashManifestTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        base = Path(temporary.name)
        root = base / "data"
        root.mkdir()
        (root / "nested").mkdir()
        (root / "alpha.txt").write_bytes(b"alpha\n")
        (root / "nested" / "beta.bin").write_bytes(b"\x00\x01\xff")
        return temporary, root, base / "manifest.json"

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def test_create_is_deterministic_and_sorted(self):
        temp, root, manifest = self.fixture()
        with temp:
            report = tool.create_manifest(root, manifest)
            first = manifest.read_bytes()
            tool.create_manifest(root, manifest, force=True)
            self.assertEqual(first, manifest.read_bytes())
            document = json.loads(first)
            self.assertEqual([x["path"] for x in document["files"]],
                             ["alpha.txt", "nested/beta.bin"])
            self.assertEqual(report["total_bytes"], 9)

    def test_manifest_inside_root_excludes_itself(self):
        temp, root, _ = self.fixture()
        with temp:
            manifest = root / "checksums.json"
            tool.create_manifest(root, manifest)
            paths = [x["path"] for x in json.loads(manifest.read_text())["files"]]
            self.assertNotIn("checksums.json", paths)
            self.assertTrue(tool.verify_manifest(root, manifest, check_extra=True)["ok"])

    def test_verify_clean_tree(self):
        temp, root, manifest = self.fixture()
        with temp:
            tool.create_manifest(root, manifest)
            report = tool.verify_manifest(root, manifest)
            self.assertTrue(report["ok"])
            self.assertEqual(report["matched_file_count"], 2)

    def test_modified_and_missing_files(self):
        temp, root, manifest = self.fixture()
        with temp:
            tool.create_manifest(root, manifest)
            (root / "alpha.txt").write_bytes(b"changed")
            (root / "nested" / "beta.bin").unlink()
            report = tool.verify_manifest(root, manifest)
            self.assertEqual([x["code"] for x in report["issues"]],
                             ["modified", "missing"])

    def test_extra_files_are_optional(self):
        temp, root, manifest = self.fixture()
        with temp:
            tool.create_manifest(root, manifest)
            (root / "later.txt").write_text("later")
            self.assertTrue(tool.verify_manifest(root, manifest)["ok"])
            report = tool.verify_manifest(root, manifest, check_extra=True)
            self.assertEqual(report["issues"][0]["code"], "extra")

    def test_symlinks_are_never_followed(self):
        temp, root, manifest = self.fixture()
        with temp:
            (root / "link").symlink_to(root / "alpha.txt")
            (root / "linked-dir").symlink_to(root / "nested", target_is_directory=True)
            report = tool.create_manifest(root, manifest)
            self.assertEqual(report["skipped_symlink_count"], 2)
            self.assertEqual(len(json.loads(manifest.read_text())["files"]), 2)

    def test_expected_file_replaced_by_symlink_is_type_mismatch(self):
        temp, root, manifest = self.fixture()
        with temp:
            tool.create_manifest(root, manifest)
            (root / "alpha.txt").unlink()
            (root / "alpha.txt").symlink_to(root / "nested" / "beta.bin")
            report = tool.verify_manifest(root, manifest)
            self.assertEqual(report["issues"][0]["code"], "type_mismatch")

    def test_empty_directory_is_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "empty"
            root.mkdir()
            manifest = base / "manifest.json"
            tool.create_manifest(root, manifest)
            self.assertTrue(tool.verify_manifest(root, manifest)["ok"])

    def test_unicode_and_space_filename_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "data"
            root.mkdir()
            (root / "catatan kucing-猫.txt").write_text("meong", encoding="utf-8")
            manifest = base / "manifest.json"
            tool.create_manifest(root, manifest)
            document = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(document["files"][0]["path"], "catatan kucing-猫.txt")
            self.assertTrue(tool.verify_manifest(root, manifest)["ok"])

    def test_manifest_overwrite_requires_force(self):
        temp, root, manifest = self.fixture()
        with temp:
            tool.create_manifest(root, manifest)
            with self.assertRaises(tool.ToolError):
                tool.create_manifest(root, manifest)
            tool.create_manifest(root, manifest, force=True)

    def test_malicious_and_duplicate_manifest_paths_are_rejected(self):
        temp, root, manifest = self.fixture()
        base = {"format": tool.FORMAT, "algorithm": "sha256", "files": []}
        with temp:
            for bad in ("../outside", "/absolute", "a\\b", "line\nbreak", "a//b"):
                with self.subTest(path=bad):
                    base["files"] = [{"path": bad, "size": 0, "sha256": "0" * 64}]
                    manifest.write_text(json.dumps(base))
                    with self.assertRaises(tool.ToolError):
                        tool.load_manifest(manifest)
            base["files"] = [{"path": "same", "size": 0, "sha256": "0" * 64}] * 2
            manifest.write_text(json.dumps(base))
            with self.assertRaises(tool.ToolError):
                tool.load_manifest(manifest)

    def test_invalid_schema_size_and_digest_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / "manifest.json"
            invalid = [
                {},
                {"format": tool.FORMAT, "algorithm": "md5", "files": []},
                {"format": tool.FORMAT, "algorithm": "sha256", "files":
                 [{"path": "a", "size": True, "sha256": "0" * 64}]},
                {"format": tool.FORMAT, "algorithm": "sha256", "files":
                 [{"path": "a", "size": 0, "sha256": "ABC"}]},
            ]
            for document in invalid:
                with self.subTest(document=document):
                    manifest.write_text(json.dumps(document))
                    with self.assertRaises(tool.ToolError):
                        tool.load_manifest(manifest)

    def test_issue_cap_keeps_full_count(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "data"
            root.mkdir()
            for number in range(50):
                (root / f"{number}.txt").write_text(str(number))
            manifest = base / "manifest.json"
            tool.create_manifest(root, manifest)
            for path in root.iterdir():
                path.unlink()
            report = tool.verify_manifest(root, manifest, max_issues=2)
            self.assertEqual(report["error_count"], 50)
            self.assertEqual(len(report["issues"]), 2)
            self.assertEqual(report["omitted_issue_count"], 48)

    def test_cli_create_verify_json_and_exit_codes(self):
        temp, root, manifest = self.fixture()
        with temp:
            created = self.cli("create", root, manifest, "--json")
            self.assertEqual(created.returncode, 0)
            self.assertEqual(json.loads(created.stdout)["file_count"], 2)
            verified = self.cli("verify", root, manifest, "--check-extra", "--json")
            self.assertEqual(verified.returncode, 0)
            (root / "alpha.txt").write_text("changed")
            self.assertEqual(self.cli("verify", root, manifest).returncode, 1)
            self.assertEqual(self.cli("create", root, manifest).returncode, 2)

    def test_cli_bad_root_manifest_and_argument_exit_two(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            missing = base / "missing"
            manifest = base / "manifest.json"
            self.assertEqual(self.cli("create", missing, manifest).returncode, 2)
            base.joinpath("data").mkdir()
            manifest.write_text("not-json")
            self.assertEqual(self.cli("verify", base / "data", manifest).returncode, 2)
            self.assertEqual(self.cli("verify", base / "data", manifest,
                                      "--max-issues", "-1").returncode, 2)


if __name__ == "__main__":
    unittest.main()
