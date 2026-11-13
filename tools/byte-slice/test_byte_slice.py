import io
import unittest

from byte_slice import copy_slice


class ByteSliceTests(unittest.TestCase):
    def test_binary_across_chunks(self):
        data = bytes(range(256)) * 300
        output = io.BytesIO()
        copy_slice(io.BytesIO(data), output, 13, 70000)
        self.assertEqual(output.getvalue(), data[13:70013])

    def test_truncated_at_eof(self):
        output = io.BytesIO()
        copy_slice(io.BytesIO(b"abc"), output, 1, 100)
        self.assertEqual(output.getvalue(), b"bc")

    def test_empty_slices(self):
        for offset, length in [(0, 0), (3, 1), (4, 1)]:
            with self.subTest(offset=offset, length=length):
                output = io.BytesIO()
                copy_slice(io.BytesIO(b"abc"), output, offset, length)
                self.assertEqual(output.getvalue(), b"")
