import codecs
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from list_compare import MAX_INPUT, compare_values, read_values

SCRIPT = Path(__file__).with_name("list_compare.py")


class ListTests(unittest.TestCase):
    def test_empty_lists(self):
        result = compare_values([], [])
        self.assertTrue(result["same_membership"])
        self.assertEqual(result["common"], [])
        self.assertEqual(result["left_lines"], 0)

    def test_membership_and_first_seen_order(self):
        result = compare_values(["c", "b", "a", "b"], ["b", "d", "a", "e", "d"])
        self.assertEqual(result["only_left"], ["c"])
        self.assertEqual(result["only_right"], ["d", "e"])
        self.assertEqual(result["common"], ["b", "a"])
        self.assertEqual((result["left_lines"], result["left_unique"],
                          result["right_lines"], result["right_unique"]), (4, 3, 5, 4))

    def test_reordering_and_duplicates_do_not_change_membership(self):
        self.assertTrue(compare_values(["a", "b", "a"], ["b", "a"])["same_membership"])

    def test_case_spaces_and_unicode_not_normalized(self):
        result = compare_values(["a", " a", "A", "é"], ["a", "a ", "e\u0301"])
        self.assertEqual(result["only_left"], [" a", "A", "é"])
        self.assertEqual(result["only_right"], ["a ", "e\u0301"])

    def test_lf_crlf_and_unterminated_last_line(self):
        self.assertEqual(read_values(io.BytesIO(b"a\r\nb\nc")), ["a", "b", "c"])
        self.assertEqual(read_values(io.BytesIO(b"a\r")), ["a\r"])
        self.assertEqual(read_values(io.BytesIO(b"a\r\rb\n")), ["a\r\rb"])

    def test_blank_lines_are_values_not_extra_trailing_records(self):
        for data, expected in [(b"", []), (b"\n", [""]), (b"a\n", ["a"]),
                               (b"a\n\n", ["a", ""]), (b"\r\n", [""])]:
            self.assertEqual(read_values(io.BytesIO(data)), expected)

    def test_bom_and_other_separators(self):
        self.assertEqual(read_values(io.BytesIO(codecs.BOM_UTF8 + "猫\u2028x\n".encode())),
                         ["猫\u2028x"])
        self.assertEqual(read_values(io.BytesIO(codecs.BOM_UTF8)), [])

    def test_invalid_utf8_and_size_limit(self):
        with self.assertRaises(ValueError):
            read_values(io.BytesIO(b"\xff"))
        self.assertEqual(len(read_values(io.BytesIO(b"a" * MAX_INPUT))[0]), MAX_INPUT)
        with self.assertRaises(ValueError):
            read_values(io.BytesIO(b"a" * (MAX_INPUT + 1)))

    def test_cli_difference_and_no_source_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            left, right = Path(folder) / "left", Path(folder) / "right"
            left.write_bytes(b"a\nb\n")
            right.write_bytes(b"b\nc\n")
            run = subprocess.run([sys.executable, str(SCRIPT), str(left), str(right)],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            result = json.loads(run.stdout)
            self.assertEqual(result["only_right"], ["c"])
            self.assertEqual(left.read_bytes(), b"a\nb\n")
            self.assertEqual(right.read_bytes(), b"b\nc\n")

    def test_cli_stdin_and_only_arrays(self):
        with tempfile.TemporaryDirectory() as folder:
            right = Path(folder) / "right"
            right.write_bytes(b"b\nc\n")
            for option, expected in [("left", ["a"]), ("right", ["c"]), ("common", ["b"])]:
                run = subprocess.run([sys.executable, str(SCRIPT), "-", str(right), "--only", option],
                                     input=b"a\nb\n", capture_output=True)
                self.assertEqual(run.returncode, 1)
                self.assertEqual(json.loads(run.stdout), expected)
            run = subprocess.run([sys.executable, str(SCRIPT), str(right), "-"],
                                 input=b"c\nb\nb\n", capture_output=True)
            self.assertEqual(run.returncode, 0)

    def test_cli_errors_have_no_report(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "bad"
            bad.write_bytes(b"\xff")
            for args in [["-", "-"], [str(bad), str(bad)],
                         [str(bad.with_name("missing")), str(bad)]]:
                run = subprocess.run([sys.executable, str(SCRIPT)] + args,
                                     capture_output=True, input=b"")
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, b"")
                self.assertTrue(run.stderr)

    def test_json_escapes_control_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "list"
            path.write_bytes(b"\x1b[31m\n")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path), str(path)],
                                 capture_output=True)
            self.assertEqual(run.returncode, 0)
            self.assertNotIn(b"\x1b", run.stdout)
            self.assertEqual(json.loads(run.stdout)["common"], ["\x1b[31m"])


if __name__ == "__main__":
    unittest.main()
