import unittest

from srt_shift import shift


class ShiftTests(unittest.TestCase):
    def test_crlf_two_cues_and_settings(self):
        source = ("1\r\n00:00:59,900 --> 00:01:01,000 X1:2\r\nHello\r\nWorld\r\n\r\n"
                  "2\r\n00:01:02,000 --> 00:01:03,000\r\nNext\r\n")
        expected = ("1\n00:01:00,100 --> 00:01:01,200 X1:2\nHello\nWorld\n\n"
                    "2\n00:01:02,200 --> 00:01:03,200\nNext\n")
        self.assertEqual(shift(source, 200), expected)

    def test_negative_offset_to_zero(self):
        self.assertIn("00:00:00,000 --> 00:00:00,500",
                      shift("1\n00:00:00,500 --> 00:00:01,000\nHi", -500))

    def test_rejects_invalid_intervals_and_syntax(self):
        for line, offset in [
            ("00:00:00,000 --> 00:00:01,000", -1),
            ("00:00:02,000 --> 00:00:01,000", 0),
            ("00:00:60,000 --> 00:01:01,000", 0),
        ]:
            with self.subTest(line=line), self.assertRaises(ValueError):
                shift(f"1\n{line}\nHi", offset)
