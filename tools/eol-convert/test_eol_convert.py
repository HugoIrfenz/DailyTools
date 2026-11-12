import io
import unittest

from eol_convert import convert


class ConvertTests(unittest.TestCase):
    def test_mixed_endings_and_unterminated_last_line(self):
        for size in (1, 2, 3, 65536):
            for ending in (b"\n", b"\r\n", b"\r"):
                with self.subTest(size=size, ending=ending):
                    output = io.BytesIO()
                    convert(io.BytesIO(b"a\r\nb\rc\n\xff"), output, ending, size)
                    self.assertEqual(output.getvalue(), ending.join((b"a", b"b", b"c", b"\xff")))

    def test_final_cr_and_empty_input(self):
        for original, expected in ((b"a\r\r", b"a\n\n"), (b"", b"")):
            output = io.BytesIO()
            convert(io.BytesIO(original), output, b"\n", 1)
            self.assertEqual(output.getvalue(), expected)
