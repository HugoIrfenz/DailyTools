import json
import subprocess
import sys
import unittest
from pathlib import Path

from unix_mode import UnixModeError, describe, format_symbolic, parse_mode


SCRIPT = Path(__file__).with_name("unix_mode.py")


class UnixModeTests(unittest.TestCase):
    def test_parses_three_digit_octal(self):
        self.assertEqual(parse_mode("755"), 0o755)

    def test_parses_four_digit_octal(self):
        self.assertEqual(parse_mode("4755"), 0o4755)

    def test_parses_octal_with_extra_prefix_zero(self):
        self.assertEqual(parse_mode("04755"), 0o4755)

    def test_formats_regular_permissions(self):
        self.assertEqual(format_symbolic(0o754), "rwxr-xr--")

    def test_formats_setuid_with_execute(self):
        self.assertEqual(format_symbolic(0o4755), "rwsr-xr-x")

    def test_formats_setuid_without_execute(self):
        self.assertEqual(format_symbolic(0o4644), "rwSr--r--")

    def test_formats_setgid(self):
        self.assertEqual(format_symbolic(0o2750), "rwxr-s---")

    def test_formats_sticky_bit(self):
        self.assertEqual(format_symbolic(0o1777), "rwxrwxrwt")

    def test_formats_sticky_without_execute(self):
        self.assertEqual(format_symbolic(0o1666), "rw-rw-rwT")

    def test_parses_symbolic_permissions(self):
        self.assertEqual(parse_mode("rwxr-xr--"), 0o754)

    def test_parses_symbolic_special_bits(self):
        self.assertEqual(parse_mode("rwsr-sr-t"), 0o7755)
        self.assertEqual(parse_mode("rwSr--r-T"), 0o5644)

    def test_round_trip_all_modes(self):
        for mode in range(0o10000):
            self.assertEqual(parse_mode(format_symbolic(mode)), mode)

    def test_describe_reports_special_flags(self):
        item = describe("2755")
        self.assertEqual(item["octal"], "2755")
        self.assertEqual(item["symbolic"], "rwxr-sr-x")
        self.assertEqual(item["special"], {"setuid": False, "setgid": True, "sticky": False})

    def test_rejects_invalid_octal_digit(self):
        with self.assertRaisesRegex(UnixModeError, "invalid octal mode"):
            parse_mode("895")

    def test_rejects_file_type_prefix(self):
        with self.assertRaises(UnixModeError):
            parse_mode("-rwxr-xr-x")

    def test_rejects_invalid_special_position(self):
        with self.assertRaises(UnixModeError):
            parse_mode("rwt------")

    def test_cli_text_multiple_modes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "755", "rw-r-----"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "755: 0755 rwxr-xr-x\nrw-r-----: 0640 rw-r-----\n")

    def test_cli_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "4755", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)[0]["special"]["setuid"])

    def test_cli_invalid_mode(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "888"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid octal mode", result.stderr)


if __name__ == "__main__":
    unittest.main()
