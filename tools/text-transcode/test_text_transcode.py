import codecs
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from text_transcode import MAX_INPUT, read_limited, transcode

SCRIPT = Path(__file__).with_name("text_transcode.py")


class TranscodeTests(unittest.TestCase):
    def test_utf8_to_latin1_and_back(self):
        self.assertEqual(transcode(b"caf\xc3\xa9", "utf-8", "latin-1"), b"caf\xe9")
        self.assertEqual(transcode(b"caf\xe9", "latin-1", "utf-8"), b"caf\xc3\xa9")

    def test_explicit_utf16_byte_orders(self):
        for encoding in ["utf-16-le", "utf-16-be"]:
            data = "猫🌼".encode(encoding)
            self.assertEqual(transcode(data, encoding, "utf-8"), "猫🌼".encode("utf-8"))
            self.assertEqual(transcode("猫🌼".encode("utf-8"), "utf-8", encoding), data)

    def test_utf16_bom_selects_input_order(self):
        for bom, encoding in [(codecs.BOM_UTF16_LE, "utf-16-le"),
                               (codecs.BOM_UTF16_BE, "utf-16-be")]:
            self.assertEqual(transcode(bom + "abc".encode(encoding), "utf-16", "utf-8"), b"abc")
        with self.assertRaises(ValueError):
            transcode(b"a\x00b\x00", "utf-16", "utf-8")

    def test_explicit_utf16_preserves_bom_as_text(self):
        self.assertEqual(transcode(codecs.BOM_UTF16_LE + b"a\x00", "utf-16-le", "utf-8"),
                         codecs.BOM_UTF8 + b"a")

    def test_utf8_sig_bom_behavior(self):
        self.assertEqual(transcode(codecs.BOM_UTF8 + b"abc", "utf-8-sig", "utf-8"), b"abc")
        self.assertEqual(transcode(b"abc", "utf-8-sig", "utf-8"), b"abc")
        self.assertEqual(transcode(b"abc", "utf-8", "utf-8-sig"), codecs.BOM_UTF8 + b"abc")
        self.assertEqual(transcode(b"", "utf-8", "utf-8-sig"), codecs.BOM_UTF8)

    def test_empty_and_ascii(self):
        self.assertEqual(transcode(b"", "utf-8", "utf-8"), b"")
        self.assertEqual(transcode(b"plain", "ascii", "utf-8"), b"plain")

    def test_newlines_and_nul_not_normalized(self):
        original = b"a\r\nb\rc\n\x00"
        encoded = transcode(original, "utf-8", "utf-16-le")
        self.assertEqual(transcode(encoded, "utf-16-le", "utf-8"), original)

    def test_invalid_input_rejected_without_bytes_in_error(self):
        for data, encoding in [(b"secret\xff", "utf-8"), (b"\xff", "ascii"),
                               (b"a", "utf-16-le"), (b"\x00\xd8", "utf-16-le")]:
            with self.subTest(encoding=encoding), self.assertRaises(ValueError) as error:
                transcode(data, encoding, "utf-8")
            self.assertEqual(str(error.exception), f"input is not valid {encoding}")

    def test_unrepresentable_output_and_unsupported_codec(self):
        for encoding in ["ascii", "latin-1"]:
            with self.assertRaises(ValueError):
                transcode("猫".encode("utf-8"), "utf-8", encoding)
        with self.assertRaises(ValueError):
            transcode(b"a", "rot13", "utf-8")

    def test_real_input_limit(self):
        self.assertEqual(len(read_limited(io.BytesIO(b"a" * MAX_INPUT))), MAX_INPUT)
        with self.assertRaises(ValueError):
            read_limited(io.BytesIO(b"a" * (MAX_INPUT + 1)))

    def test_cli_stdin_binary_output_no_added_newline(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "--from", "utf-8", "--to", "utf-16-be"],
                             input=b"hello\r\n", capture_output=True)
        self.assertEqual((run.returncode, run.stdout, run.stderr),
                         (0, "hello\r\n".encode("utf-16-be"), b""))

    def test_cli_file_does_not_modify_source(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.txt"
            path.write_bytes(b"caf\xe9")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path), "--from", "latin-1",
                                  "--to", "utf-8"], capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (0, b"caf\xc3\xa9"))
            self.assertEqual(path.read_bytes(), b"caf\xe9")

    def test_cli_errors_produce_no_partial_output(self):
        for data, target in [(b"PRIVATE-PREFIX\xff", "utf-8"), ("PRIVATE-PREFIX 猫".encode("utf-8"), "ascii")]:
            run = subprocess.run([sys.executable, str(SCRIPT), "--from", "utf-8", "--to", target],
                                 input=data, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, b"")
            self.assertNotIn(b"PRIVATE-PREFIX", run.stderr)

    def test_cli_missing_file_and_bad_options(self):
        with tempfile.TemporaryDirectory() as folder:
            cases = [[str(Path(folder) / "missing"), "--from", "utf-8", "--to", "utf-8"],
                     ["--from", "guess", "--to", "utf-8"], ["--from", "utf-8"]]
            for args in cases:
                run = subprocess.run([sys.executable, str(SCRIPT)] + args, capture_output=True)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, b"")


if __name__ == "__main__":
    unittest.main()
