import codecs
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata
import unittest

from unicode_inspect import MAX_INPUT, inspect_text, read_text

SCRIPT = Path(__file__).with_name("unicode_inspect.py")


class UnicodeTests(unittest.TestCase):
    def test_empty_and_ordinary_text(self):
        for text in ["", "hello \t world\r\n", "café 猫 🌼 e\u0301"]:
            self.assertEqual(inspect_text(text)["total"], 0)

    def test_selected_categories(self):
        result = inspect_text("\x00\x1b\u200b\u00a0\u2028\u2029")
        self.assertEqual(result["total"], 6)
        self.assertEqual([x["category"] for x in result["findings"]],
                         ["Cc", "Cc", "Cf", "Zs", "Zl", "Zp"])
        self.assertEqual(result["findings"][2]["name"], "ZERO WIDTH SPACE")
        self.assertEqual(result["findings"][0]["name"], "<unnamed>")

    def test_positions_lf_only_one_based_codepoints(self):
        result = inspect_text("猫🌼\t\u200b\r\nA\u00a0\r\x00")
        self.assertEqual([(x["line"], x["column"]) for x in result["findings"]],
                         [(1, 4), (2, 2), (2, 4)])

    def test_counts_and_bounded_findings(self):
        result = inspect_text("\u200b\x00\u200b", 1)
        self.assertEqual((result["total"], result["shown"], result["omitted"]), (3, 1, 2))
        self.assertEqual(result["counts"], {"U+0000": 1, "U+200B": 2})
        self.assertEqual(result["unicode_version"], unicodedata.unidata_version)

    def test_zero_limit_still_counts_all_matches(self):
        result = inspect_text("\u200b" * 100, 0)
        self.assertEqual(result["total"], 100)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["omitted"], 100)

    def test_bom_is_reported(self):
        text = read_text(io.BytesIO(codecs.BOM_UTF8 + b"a"))
        finding = inspect_text(text)["findings"][0]
        self.assertEqual((finding["codepoint"], finding["column"]), ("U+FEFF", 1))

    def test_supplementary_format_character(self):
        result = inspect_text("\U000e0001")
        self.assertEqual(result["findings"][0]["codepoint"], "U+E0001")
        self.assertEqual(result["findings"][0]["category"], "Cf")

    def test_variation_selectors_not_in_scope(self):
        self.assertEqual(inspect_text("\ufe0f\U000e0100")["total"], 0)

    def test_invalid_limits(self):
        for limit in [-1, 10001]:
            with self.assertRaises(ValueError):
                inspect_text("a", limit)

    def test_input_limit_and_utf8_errors(self):
        self.assertEqual(len(read_text(io.BytesIO(b"a" * MAX_INPUT))), MAX_INPUT)
        for data in [b"a" * (MAX_INPUT + 1), b"\xff"]:
            with self.assertRaises(ValueError):
                read_text(io.BytesIO(data))

    def test_cli_stdin_json_reports_without_raw_character(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "--json", "--limit", "1"],
                             input="a\u200bb\u00a0".encode(), capture_output=True)
        self.assertEqual(run.returncode, 1)
        result = json.loads(run.stdout)
        self.assertEqual((result["total"], result["omitted"]), (2, 1))
        self.assertEqual(result["findings"][0]["column"], 2)
        self.assertNotIn("\u200b".encode(), run.stdout)

    def test_cli_file_text_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data"
            original = b"abc\x1b"
            path.write_bytes(original)
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("1:4 U+001B Cc", run.stdout)
            self.assertNotIn("\x1b", run.stdout)
            self.assertEqual(path.read_bytes(), original)

    def test_cli_clean_exit_and_errors(self):
        run = subprocess.run([sys.executable, str(SCRIPT)], input=b"clean\n", capture_output=True)
        self.assertEqual(run.returncode, 0)
        cases = [([], b"\xff"), (["--limit", "-1"], b""),
                 (["--limit", "10001"], b""), (["--limit", "bad"], b"")]
        with tempfile.TemporaryDirectory() as folder:
            cases.append(([str(Path(folder) / "missing")], b""))
            for args, data in cases:
                run = subprocess.run([sys.executable, str(SCRIPT)] + args, input=data, capture_output=True)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, b"")


if __name__ == "__main__":
    unittest.main()
