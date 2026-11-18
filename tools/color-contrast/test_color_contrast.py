import argparse
import subprocess
import sys
import unittest
from pathlib import Path

from color_contrast import color, contrast


class ContrastTests(unittest.TestCase):
    def test_extremes_and_symmetry(self):
        black, white = color("#000"), color("ffffff")
        self.assertEqual(contrast(black, white), 21)
        self.assertEqual(contrast(white, black), 21)
        self.assertEqual(contrast(white, white), 1)

    def test_nontrivial_weights_and_dark_gray(self):
        self.assertAlmostEqual(contrast(color("f00"), color("fff")), 3.99847677)
        self.assertAlmostEqual(contrast(color("0a0a0a"), color("000")), 1.0607054)

    def test_bad_hex(self):
        for value in ("ffff", "12345678", "red", "##fff", "fff\n"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                color(value)

    def test_cli(self):
        script = Path(__file__).with_name("color_contrast.py")
        result = subprocess.check_output([sys.executable, script, "#000", "#FFF"], text=True)
        self.assertEqual(result, "21.0000:1\n")
