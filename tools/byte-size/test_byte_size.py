import json
from pathlib import Path
import subprocess
import sys
import unittest

from byte_size import human_size, parse_size

SCRIPT = Path(__file__).with_name("byte_size.py")


class SizeTests(unittest.TestCase):
    def test_bare_bytes_and_zero(self):
        self.assertEqual(parse_size("1024"), 1024)
        self.assertEqual(parse_size("0 B"), 0)
        self.assertEqual(parse_size("  001.0B  "), 1)

    def test_decimal_units(self):
        for power, unit in enumerate(["B", "kB", "MB", "GB", "TB", "PB", "EB"]):
            self.assertEqual(parse_size("1" + unit), 1000**power)
        self.assertEqual(parse_size("1 KB"), 1000)

    def test_binary_units(self):
        for power, unit in enumerate(["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]):
            self.assertEqual(parse_size("1" + unit), 1024**power)

    def test_exact_fraction(self):
        self.assertEqual(parse_size("1.5 GiB"), 1610612736)
        self.assertEqual(parse_size("0.001kB"), 1)
        self.assertEqual(parse_size("0.0009765625KiB"), 1)

    def test_reject_fractional_byte(self):
        for value in ["0.1B", "0.0001kB", "0.1KiB"]:
            with self.assertRaises(ValueError):
                parse_size(value)

    def test_invalid_grammar_and_case(self):
        for value in ["", "-1B", "+1B", "NaN", "inf", "1e3B", ".5GB", "1.GB",
                      "1mb", "1K", "1bit", "1 Mi B", "１B", "1GB extra"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_size(value)

    def test_length_limit(self):
        with self.assertRaises(ValueError):
            parse_size("1" * 257)

    def test_large_exact_integer(self):
        self.assertEqual(parse_size("9007199254740993B"), 9007199254740993)

    def test_unit_boundaries(self):
        self.assertEqual(human_size(999), "999 B")
        self.assertEqual(human_size(1000), "1.00 kB")
        self.assertEqual(human_size(1023, True), "1023 B")
        self.assertEqual(human_size(1024, True), "1.00 KiB")
        self.assertEqual(human_size(1024**7, True), "1024.00 EiB")

    def test_half_up_rounding_and_zero(self):
        self.assertEqual(human_size(1005), "1.01 kB")
        self.assertEqual(human_size(1004), "1.00 kB")
        self.assertEqual(human_size(0, True), "0 B")
        with self.assertRaises(ValueError):
            human_size(-1)

    def test_cli_json_and_text(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "1.5 GiB", "--json"],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(json.loads(run.stdout), {"bytes": 1610612736,
                         "decimal": "1.61 GB", "binary": "1.50 GiB"})
        run = subprocess.run([sys.executable, str(SCRIPT), "1024"], capture_output=True, text=True)
        self.assertEqual((run.returncode, run.stdout), (0, "1024 bytes | 1.02 kB | 1.00 KiB\n"))

    def test_cli_error_no_stdout(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "0.1B"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, "")
        self.assertTrue(run.stderr)


if __name__ == "__main__":
    unittest.main()
