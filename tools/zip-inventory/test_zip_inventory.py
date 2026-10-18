import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

from zip_inventory import summarize

SCRIPT = Path(__file__).with_name("zip_inventory.py")


def make_zip(members, compression=zipfile.ZIP_STORED):
    buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(buffer, "w", compression=compression) as archive:
            for name, data in members:
                archive.writestr(name, data)
    return buffer.getvalue()


def inventory(data, top=10):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return summarize(archive, top)


class InventoryTests(unittest.TestCase):
    def test_empty_archive(self):
        self.assertEqual(inventory(make_zip([])), {
            "entries": 0, "files": 0, "directories": 0,
            "uncompressed_bytes": 0, "compressed_bytes": 0, "encrypted_files": 0,
            "duplicate_names": [], "largest_files": []})

    def test_stored_files_and_directory(self):
        result = inventory(make_zip([("folder/", b""), ("folder/a", b"abc"),
                                     ("b", b"12345")]))
        self.assertEqual((result["entries"], result["files"], result["directories"]),
                         (3, 2, 1))
        self.assertEqual((result["uncompressed_bytes"], result["compressed_bytes"]),
                         (8, 8))
        self.assertEqual([x["name"] for x in result["largest_files"]], ["b", "folder/a"])

    def test_deflated_sizes_match_central_directory(self):
        data = make_zip([("repeat", b"a" * 10000)], zipfile.ZIP_DEFLATED)
        result = inventory(data)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(result["compressed_bytes"], archive.getinfo("repeat").compress_size)
        self.assertEqual(result["uncompressed_bytes"], 10000)
        self.assertLess(result["compressed_bytes"], 10000)

    def test_zero_byte_file(self):
        result = inventory(make_zip([("empty", b"")]))
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["largest_files"][0]["uncompressed_bytes"], 0)

    def test_directory_records_count_in_totals_not_largest_files(self):
        result = inventory(make_zip([("folder/", b"abc"), ("folder/", b"d")]))
        self.assertEqual((result["files"], result["directories"]), (0, 2))
        self.assertEqual(result["uncompressed_bytes"], 4)
        self.assertEqual(result["largest_files"], [])
        self.assertEqual(result["duplicate_names"], [{"name": "folder/", "count": 2}])

    def test_truncated_archive(self):
        data = make_zip([("a", b"hello")])
        with self.assertRaises(zipfile.BadZipFile):
            inventory(data[:-12])

    def test_duplicate_names_retained_as_separate_entries(self):
        result = inventory(make_zip([("same", b"abc"), ("same", b"abcdef")]))
        self.assertEqual(result["duplicate_names"], [{"name": "same", "count": 2}])
        self.assertEqual(result["uncompressed_bytes"], 9)
        self.assertEqual([x["entry_index"] for x in result["largest_files"]], [1, 0])

    def test_tie_order_is_name_then_original_index(self):
        result = inventory(make_zip([("z", b"x"), ("a", b"x"), ("a", b"x")]))
        self.assertEqual([x["entry_index"] for x in result["largest_files"]], [1, 2, 0])

    def test_top_zero_and_limit(self):
        data = make_zip([("a", b"x"), ("b", b"xx")])
        self.assertEqual(inventory(data, 0)["largest_files"], [])
        self.assertEqual(len(inventory(data, 1)["largest_files"]), 1)
        self.assertEqual(inventory(data, 0)["files"], 2)
        for top in [-1, 1001]:
            with self.assertRaises(ValueError):
                inventory(data, top)

    def test_unicode_and_exact_names(self):
        result = inventory(make_zip([("kucing-猫", b"x"), ("A", b""), ("a", b"")]))
        self.assertEqual(result["largest_files"][0]["name"], "kucing-猫")
        self.assertEqual(result["duplicate_names"], [])

    def test_encryption_flag_from_actual_directory_bytes(self):
        data = bytearray(make_zip([("a", b"hello")]))
        central = data.index(b"PK\x01\x02")
        flags = struct.unpack_from("<H", data, central + 8)[0]
        struct.pack_into("<H", data, central + 8, flags | 1)
        # Metadata fixture only; the payload is not actually encrypted.
        result = inventory(data)
        self.assertEqual(result["encrypted_files"], 1)
        self.assertTrue(result["largest_files"][0]["encrypted"])

    def test_damaged_payload_is_not_read_or_crc_checked(self):
        data = bytearray(make_zip([("a", b"hello")]))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = archive.getinfo("a")
            offset = info.header_offset
            name_len, extra_len = struct.unpack_from("<HH", data, offset + 26)
            data[offset + 30 + name_len + extra_len] ^= 255
        self.assertEqual(inventory(data)["uncompressed_bytes"], 5)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            with self.assertRaises(zipfile.BadZipFile):
                archive.read("a")

    def test_cli_json_and_no_extraction_or_modification(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.zip"
            original = make_zip([("../outside.txt", b"x"), ("nested/a", b"123")])
            path.write_bytes(original)
            run = subprocess.run([sys.executable, str(SCRIPT), str(path), "--json", "--top", "1"],
                                 capture_output=True, text=True, cwd=folder)
            self.assertEqual(run.returncode, 0)
            result = json.loads(run.stdout)
            self.assertEqual(result["largest_files"][0]["name"], "nested/a")
            self.assertEqual(result["entries"], 2)
            self.assertEqual(list(Path(folder).iterdir()), [path])
            self.assertEqual(path.read_bytes(), original)

    def test_cli_escapes_control_characters_in_names(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.zip"
            path.write_bytes(make_zip([("a\n\x1b[31m", b"x")]))
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0)
            self.assertNotIn("\x1b", run.stdout)
            self.assertIn('"a\\n\\u001b[31m"', run.stdout)

    def test_cli_bad_archives_and_arguments(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.zip"
            path.write_bytes(b"not a zip")
            cases = [[str(path)], [str(path.with_name("missing.zip"))], [folder],
                     [str(path), "--top", "-1"], [str(path), "--top", "1001"],
                     [str(path), "--top", "nope"]]
            for args in cases:
                with self.subTest(args=args):
                    run = subprocess.run([sys.executable, str(SCRIPT)] + args,
                                         capture_output=True, text=True)
                    self.assertEqual(run.returncode, 2)
                    self.assertEqual(run.stdout, "")
                    self.assertTrue(run.stderr)


if __name__ == "__main__":
    unittest.main()
