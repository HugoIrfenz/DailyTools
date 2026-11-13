import unittest

from query_encode import encode


class EncodeTests(unittest.TestCase):
    def test_order_duplicates_and_empty_values(self):
        self.assertEqual(encode(["q=kopi susu", "tag=go", "tag=c++", "x="]),
                         "q=kopi+susu&tag=go&tag=c%2B%2B&x=")

    def test_unicode_delimiters_and_literal_percent(self):
        self.assertEqual(encode(["café=a=b&c%20"]), "caf%C3%A9=a%3Db%26c%2520")

    def test_invalid_pairs(self):
        for pair in ["missing", "=value"]:
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                encode([pair])
