import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from tar_inventory import render_text, summarize, suspicious_entry, unsafe_path_reason


SCRIPT = Path(__file__).with_name("tar_inventory.py")


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    archive.addfile(info, io.BytesIO(data))


class TarInventoryTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def make_archive(self, path: Path, mode: str = "w") -> None:
        with tarfile.open(path, mode) as archive:
            directory = tarfile.TarInfo("docs")
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
            add_bytes(archive, "small.txt", b"a")
            add_bytes(archive, "docs/large.bin", b"12345")
            link = tarfile.TarInfo("latest")
            link.type = tarfile.SYMTYPE
            link.linkname = "docs/large.bin"
            archive.addfile(link)

    def test_summarizes_entry_types_and_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.tar")
            self.make_archive(path)
            result = summarize(path)
        self.assertEqual(result["members"], 4)
        self.assertEqual(result["regular_files"], 2)
        self.assertEqual(result["directories"], 1)
        self.assertEqual(result["symlinks"], 1)
        self.assertEqual(result["logical_file_bytes"], 6)

    def test_largest_files_are_sorted_by_size(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.tar")
            self.make_archive(path)
            result = summarize(path, top=1)
        self.assertEqual(result["largest_files"], [{"name": "docs/large.bin", "size": 5}])

    def test_top_zero_omits_largest_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.tar")
            self.make_archive(path)
            result = summarize(path, top=0)
        self.assertEqual(result["largest_files"], [])

    def test_reads_gzip_compressed_tar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.tar.gz")
            self.make_archive(path, "w:gz")
            result = summarize(path)
        self.assertEqual(result["regular_files"], 2)

    def test_duplicate_names_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "duplicate.tar")
            with tarfile.open(path, "w") as archive:
                add_bytes(archive, "same.txt", b"one")
                add_bytes(archive, "same.txt", b"two")
            result = summarize(path)
        self.assertEqual(result["duplicate_names"], [{"name": "same.txt", "count": 2}])

    def test_parent_traversal_is_suspicious(self) -> None:
        self.assertEqual(unsafe_path_reason("../escape.txt"), "parent traversal")

    def test_absolute_paths_are_suspicious(self) -> None:
        self.assertEqual(unsafe_path_reason("/etc/passwd"), "absolute path")
        self.assertEqual(unsafe_path_reason("C:\\temp\\x"), "absolute path")

    def test_safe_relative_path_is_not_suspicious(self) -> None:
        self.assertIsNone(unsafe_path_reason("docs/report.txt"))

    def test_unsafe_link_target_is_suspicious(self) -> None:
        info = tarfile.TarInfo("link")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../outside"
        self.assertEqual(
            suspicious_entry(info),
            {"name": "link", "reason": "link target: parent traversal"},
        )

    def test_special_entry_counts_as_other(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "special.tar")
            with tarfile.open(path, "w") as archive:
                info = tarfile.TarInfo("pipe")
                info.type = tarfile.FIFOTYPE
                archive.addfile(info)
            result = summarize(path)
        self.assertEqual(result["other_entries"], 1)

    def test_text_output_contains_counts(self) -> None:
        rendered = render_text({
            "archive": "a.tar", "members": 0, "regular_files": 0, "directories": 0,
            "symlinks": 0, "hardlinks": 0, "other_entries": 0,
            "logical_file_bytes": 0, "duplicate_names": [],
            "suspicious_entries": [], "largest_files": [],
        })
        self.assertIn("members: 0", rendered)
        self.assertIn("suspicious entries: 0", rendered)

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.tar")
            self.make_archive(path)
            result = self.run_cli(str(path), "--top", "1", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["largest_files"][0]["name"], "docs/large.bin")

    def test_cli_text_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.tar")
            self.make_archive(path)
            result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 0)
        self.assertIn("regular files: 2", result.stdout)

    def test_cli_rejects_corrupt_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "bad.tar")
            path.write_bytes(b"not a tar archive")
            result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_cli_reports_missing_archive(self) -> None:
        result = self.run_cli("missing.tar")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_cli_rejects_negative_top(self) -> None:
        result = self.run_cli("missing.tar", "--top", "-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("non-negative", result.stderr)


if __name__ == "__main__":
    unittest.main()
