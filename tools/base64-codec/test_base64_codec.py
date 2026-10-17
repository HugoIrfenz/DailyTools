import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from base64_codec import MAX_INPUT, decode, encode, read_limited

SCRIPT = Path(__file__).with_name("base64_codec.py")


class CodecTests(unittest.TestCase):
    def test_known_vectors(self):
        for raw, coded in [(b"", b""), (b"f", b"Zg=="), (b"fo", b"Zm8="),
                           (b"foo", b"Zm9v"), (b"hello", b"aGVsbG8=")]:
            self.assertEqual(encode(raw), coded)
            self.assertEqual(decode(coded), raw)

    def test_all_bytes_roundtrip(self):
        raw = bytes(range(256)) * 19
        for urlsafe in [False, True]:
            self.assertEqual(decode(encode(raw, urlsafe), urlsafe), raw)

    def test_urlsafe_alphabet(self):
        self.assertEqual(encode(b"\xfb\xff", True), b"-_8=")
        self.assertEqual(decode(b"-_8=", True), b"\xfb\xff")
        for coded, mode in [(b"+/8=", True), (b"-_8=", False)]:
            with self.assertRaises(ValueError):
                decode(coded, mode)

    def test_whitespace(self):
        self.assertEqual(decode(b" Z\tg\r\n== \n"), b"f")
        self.assertEqual(decode(b" \r\n\t"), b"")

    def test_padding_and_invalid_characters(self):
        for coded in [b"Zg", b"Zg=", b"Zg===", b"=Zg=", b"Z=g=", b"Zg==x",
                      b"a", b"====", b"Zm9v=", b"Zg==\xff", b"Zg==\v"]:
            with self.subTest(coded=coded), self.assertRaises(ValueError):
                decode(coded)

    def test_reject_nonzero_unused_bits(self):
        for coded in [b"Zh==", b"Zm9=", b"__9="]:
            with self.assertRaises(ValueError):
                decode(coded, coded.startswith(b"_"))

    def test_input_size_boundary(self):
        self.assertEqual(len(read_limited(io.BytesIO(b"a" * MAX_INPUT))), MAX_INPUT)
        with self.assertRaises(ValueError):
            read_limited(io.BytesIO(b"a" * (MAX_INPUT + 1)))

    def test_cli_binary_stdin(self):
        raw = b"\x00\xff\r\n"
        enc = subprocess.run([sys.executable, str(SCRIPT), "encode"], input=raw,
                             capture_output=True)
        self.assertEqual(enc.returncode, 0)
        self.assertEqual(enc.stdout, encode(raw) + b"\n")
        dec = subprocess.run([sys.executable, str(SCRIPT), "decode"], input=enc.stdout,
                             capture_output=True)
        self.assertEqual((dec.returncode, dec.stdout), (0, raw))

    def test_cli_file_and_urlsafe(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bytes"
            path.write_bytes(b"\xfb\xff")
            run = subprocess.run([sys.executable, str(SCRIPT), "encode", str(path),
                                  "--urlsafe"], capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (0, b"-_8=\n"))
            self.assertEqual(path.read_bytes(), b"\xfb\xff")

    def test_cli_error_without_partial_output(self):
        for args, data in [(["decode"], b"Zm9v\ninvalid!"),
                           (["encode", str(SCRIPT / "missing")], b"")]:
            run = subprocess.run([sys.executable, str(SCRIPT)] + args, input=data,
                                 capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, b"")
            self.assertTrue(run.stderr)


if __name__ == "__main__":
    unittest.main()
