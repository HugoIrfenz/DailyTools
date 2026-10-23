import json
import subprocess
import sys
import unittest
from pathlib import Path

from semver_compare import SemVer, SemVerError, compare


SCRIPT = Path(__file__).with_name("semver_compare.py")


class SemVerCompareTests(unittest.TestCase):
    def test_compares_core_versions(self):
        self.assertEqual(compare(SemVer.parse("1.2.3"), SemVer.parse("2.0.0")), -1)
        self.assertEqual(compare(SemVer.parse("2.1.0"), SemVer.parse("2.0.9")), 1)

    def test_release_precedes_nothing_and_follows_prerelease(self):
        self.assertGreater(SemVer.parse("1.0.0"), SemVer.parse("1.0.0-rc.1"))

    def test_numeric_prerelease_identifiers_compare_numerically(self):
        self.assertLess(SemVer.parse("1.0.0-alpha.2"), SemVer.parse("1.0.0-alpha.10"))

    def test_numeric_identifier_precedes_text_identifier(self):
        self.assertLess(SemVer.parse("1.0.0-1"), SemVer.parse("1.0.0-alpha"))

    def test_shorter_equal_prefix_precedes_longer(self):
        self.assertLess(SemVer.parse("1.0.0-alpha"), SemVer.parse("1.0.0-alpha.1"))

    def test_spec_precedence_chain(self):
        values = [
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.beta",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0",
        ]
        parsed = [SemVer.parse(value) for value in values]
        self.assertEqual(sorted(reversed(parsed)), parsed)

    def test_build_metadata_does_not_affect_precedence(self):
        left = SemVer.parse("1.0.0+one")
        right = SemVer.parse("1.0.0+two")
        self.assertEqual(left, right)
        self.assertEqual(hash(left), hash(right))

    def test_rejects_leading_zero_in_core(self):
        with self.assertRaises(SemVerError):
            SemVer.parse("01.2.3")

    def test_rejects_leading_zero_in_numeric_prerelease(self):
        with self.assertRaises(SemVerError):
            SemVer.parse("1.2.3-01")

    def test_rejects_missing_component(self):
        with self.assertRaises(SemVerError):
            SemVer.parse("1.2")

    def test_rejects_v_prefix(self):
        with self.assertRaises(SemVerError):
            SemVer.parse("v1.2.3")

    def test_cli_text(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "1.2.3", "1.3.0"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "1.2.3 < 1.3.0\n")

    def test_cli_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "1.0.0+one", "1.0.0+two", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["result"], 0)

    def test_cli_invalid_version(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "1.0", "1.0.0"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid Semantic Version", result.stderr)


if __name__ == "__main__":
    unittest.main()
