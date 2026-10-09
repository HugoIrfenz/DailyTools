import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import csv_audit as tool


SCRIPT = Path(__file__).with_name("csv_audit.py")


class CsvAuditTests(unittest.TestCase):
    def report(self, raw, **options):
        return tool.validate(io.BytesIO(raw), **options)

    def cli(self, *args, input=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=input,
                              capture_output=True)

    def test_valid_unicode_crlf_quotes_and_multiline_field(self):
        raw = 'id,note\r\n1,"hello, 猫"\r\n2,"two\nlines"'.encode()
        report = self.report(raw)
        self.assertTrue(report["ok"])
        self.assertEqual(report["data_row_count"], 2)
        self.assertEqual(report["physical_line_count"], 4)

    def test_ragged_rows_report_expected_and_actual_then_continue(self):
        report = self.report(b'a,b\n1\n2,3,4\n5,6\n')
        self.assertEqual(report["data_row_count"], 3)
        self.assertEqual(report["error_count"], 2)
        self.assertEqual(report["errors"][0]["expected"], 2)
        self.assertEqual(report["errors"][1]["actual"], 3)

    def test_blank_and_duplicate_headers_do_not_leak_names(self):
        report = self.report(b'super-secret,,super-secret\n1,2,3\n')
        encoded = json.dumps(report)
        self.assertEqual([e["code"] for e in report["errors"]],
                         ["blank_header", "duplicate_header"])
        self.assertNotIn("super-secret", encoded)

    def test_no_header_uses_first_record_as_data(self):
        report = self.report(b'1,2\n3,4\n', header=False)
        self.assertTrue(report["ok"])
        self.assertEqual(report["data_row_count"], 2)

    def test_empty_and_header_only_inputs(self):
        self.assertEqual(self.report(b'')["errors"][0]["code"], "no_records")
        report = self.report(b'a,b\n')
        self.assertEqual(report["errors"][0]["code"], "no_data_rows")
        self.assertTrue(self.report(b'1,2\n', header=False)["ok"])

    def test_utf8_bom_is_accepted(self):
        report = self.report(b'\xef\xbb\xbfid,name\n1,ok\n')
        self.assertTrue(report["ok"])
        self.assertEqual(report["column_count"], 2)

    def test_invalid_utf8_and_nul_are_reported_without_content(self):
        bad_utf8 = self.report(b'a\n\xffsecret\n')
        self.assertEqual(bad_utf8["errors"][0]["code"], "invalid_utf8")
        self.assertNotIn("secret", json.dumps(bad_utf8))
        nul = self.report(b'a\n\x00value\n')
        self.assertEqual(nul["errors"][0]["code"], "nul_byte")

    def test_malformed_csv_is_reported(self):
        report = self.report(b'a,b\n1,"unterminated\n')
        self.assertEqual(report["errors"][0]["code"], "invalid_csv")

    def test_field_size_limit_is_reported_as_csv_error(self):
        report = self.report(b'a\n123456\n', max_field_size=5)
        self.assertEqual(report["errors"][0]["code"], "invalid_csv")

    def test_error_detail_cap_does_not_stop_row_scan(self):
        raw = b'a,b\n' + b'x\n' * 1000 + b'1,2\n'
        report = self.report(raw, max_errors=2)
        self.assertEqual(report["data_row_count"], 1001)
        self.assertEqual(report["error_count"], 1000)
        self.assertEqual(report["omitted_error_count"], 998)
        self.assertEqual(len(report["errors"]), 2)

    def test_custom_delimiters(self):
        self.assertTrue(self.report(b'a\tb\n1\t2\n', delimiter='\t')["ok"])
        self.assertTrue(self.report(b'a;b\n1;2\n', delimiter=';')["ok"])

    def test_single_pass_generator(self):
        lines = (line for line in [b'a,b\n'] + [b'1,2\n'] * 3000)
        report = tool.validate(lines)
        self.assertTrue(report["ok"])
        self.assertEqual(report["data_row_count"], 3000)

    def test_cli_file_is_unchanged_and_json_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "valid.csv"
            raw = b'id,name\n1,Ada\n'
            path.write_bytes(raw)
            result = self.cli(str(path), "--json")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["data_row_count"], 1)
            self.assertEqual(path.read_bytes(), raw)

    def test_cli_stdin_validation_and_argument_exit_codes(self):
        clean = self.cli("-", "--delimiter", "tab", input=b'a\tb\n1\t2\n')
        self.assertEqual(clean.returncode, 0)
        invalid = self.cli("-", input=b'a,b\n1\n')
        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(self.cli("-", "--max-errors", "-1", input=b'').returncode, 2)
        self.assertEqual(self.cli("-", "--delimiter", "xx", input=b'').returncode, 2)

    def test_cli_read_error_is_private_and_exit_two(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.cli(str(Path(folder) / "private-name.csv"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertNotIn(b'private-name', result.stderr)


if __name__ == "__main__":
    unittest.main()
