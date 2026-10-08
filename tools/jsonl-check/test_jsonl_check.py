import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import jsonl_check as tool


SCRIPT = Path(__file__).with_name("jsonl_check.py")


class JsonlCheckTests(unittest.TestCase):
    def report(self, raw, **options):
        return tool.validate(io.BytesIO(raw), **options)

    def cli(self, *args, input=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=input,
                              capture_output=True)

    def test_all_json_types_unicode_crlf_and_final_line(self):
        raw = '{"name":"猫"}\r\n[1,2]\r\n"hi"\r\n42\r\ntrue\r\nnull'.encode()
        report = self.report(raw)
        self.assertTrue(report["ok"])
        self.assertEqual(report["valid_record_count"], 6)

    def test_objects_only(self):
        report = self.report(b'{}\n[]\nnull\n', objects_only=True)
        self.assertEqual(report["valid_record_count"], 1)
        self.assertEqual([e["line"] for e in report["errors"]], [2, 3])

    def test_blank_lines_and_empty_inputs(self):
        self.assertEqual(self.report(b'{}\n\n \n')["error_count"], 2)
        self.assertTrue(self.report(b'{}\n\n', allow_blank=True)["ok"])
        for raw in (b'', b'\n \n'):
            with self.subTest(raw=raw):
                self.assertEqual(self.report(raw, allow_blank=True)["errors"][0]["code"],
                                 "no_records")

    def test_duplicate_keys_nested_and_no_secret_in_report(self):
        raw = b'{"hidden-secret":{"private-key":1,"private-key":2}}\n'
        report = self.report(raw)
        self.assertEqual(report["errors"][0]["code"], "duplicate_key")
        self.assertNotIn("hidden-secret", json.dumps(report))
        self.assertNotIn("private-key", json.dumps(report))

    def test_nonstandard_numbers_rejected(self):
        for number in (b'NaN', b'Infinity', b'-Infinity'):
            with self.subTest(number=number):
                self.assertEqual(self.report(number)["errors"][0]["code"], "non_json_number")

    def test_exact_decimal_and_large_exponent_are_valid(self):
        report = self.report(b'0.12345678901234567890123456789\n1e400\n'
                             b'1e999999999999999999999\n' + b'9' * 5000 + b'\n')
        self.assertTrue(report["ok"])
        self.assertEqual(report["valid_record_count"], 4)

    def test_deep_nesting_reports_limit_and_continues(self):
        # CPython's C recursion threshold can differ from the Python threshold.
        depth = max(10000, sys.getrecursionlimit() * 10)
        raw = b'[' * depth + b'0' + b']' * depth
        report = self.report(raw + b'\n{}\n')
        self.assertEqual(report["errors"][0]["code"], "parser_limit")
        self.assertEqual(report["valid_record_count"], 1)

    def test_utf8_error_does_not_stop_later_records(self):
        report = self.report(b'{}\n"\xff"\n{}\n')
        self.assertEqual(report["valid_record_count"], 2)
        self.assertEqual(report["errors"][0]["line"], 2)
        self.assertEqual(report["errors"][0]["code"], "invalid_utf8")

    def test_bom_malformed_and_multiple_values(self):
        report = self.report(b'\xef\xbb\xbf{}\n{"x":}\n{} {}\n')
        self.assertEqual(report["error_count"], 3)
        self.assertEqual(report["errors"][1]["column"], 6)
        self.assertTrue(all(e["code"] == "invalid_json" for e in report["errors"]))

    def test_error_cap_keeps_scanning(self):
        report = self.report(b'bad\n' * 1000 + b'{}\n', max_errors=2)
        self.assertEqual(report["error_count"], 1000)
        self.assertEqual(report["omitted_error_count"], 998)
        self.assertEqual(report["valid_record_count"], 1)
        self.assertEqual(report["line_count"], 1001)
        self.assertEqual(len(report["errors"]), 2)

    def test_zero_error_details(self):
        report = self.report(b'bad\n', max_errors=0)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["omitted_error_count"], 1)

    def test_single_pass_iterable(self):
        report = tool.validate((b'{}\n' for _ in range(2000)))
        self.assertTrue(report["ok"])
        self.assertEqual(report["valid_record_count"], 2000)

    def test_cli_file_is_unchanged_and_json_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "valid.jsonl"
            raw = b'{"id":1}\n{"id":2}\n'
            path.write_bytes(raw)
            result = self.cli(str(path), "--json")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["valid_record_count"], 2)
            self.assertEqual(path.read_bytes(), raw)

    def test_cli_stdin_and_validation_failure(self):
        result = self.cli("-", "--json", input=b'{}\nbad\n')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["errors"][0]["line"], 2)
        clean = self.cli("-", "--allow-blank", "--objects-only", input=b'{}\n\n')
        self.assertEqual(clean.returncode, 0)

    def test_cli_io_and_argument_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.cli(str(Path(folder) / "missing"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(self.cli("-", "--max-errors", "-1", input=b'{}').returncode, 2)


if __name__ == "__main__":
    unittest.main()
