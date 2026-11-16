import io
import struct
import unittest
import zlib

from png_size import dimensions


def header(width, height):
    data = b"IHDR" + struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + data + struct.pack(">I", zlib.crc32(data))


class PNGSizeTests(unittest.TestCase):
    def test_reads_only_header(self):
        stream = io.BytesIO(header(640, 480) + b"trailing")
        self.assertEqual(dimensions(stream), (640, 480))
        self.assertEqual(stream.tell(), 33)

    def test_rejects_bad_signature_and_truncated_header(self):
        for data in (b"X" + header(1, 1)[1:], header(1, 1)[:-1]):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "signature"):
                dimensions(io.BytesIO(data))

    def test_rejects_checksum_and_dimension_errors(self):
        for data, message in ((header(1, 1)[:-4] + b"\x00" * 4, "checksum"),
                              (header(0, 1), "bounds"), (header(1, 2**31), "bounds")):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                dimensions(io.BytesIO(data))
