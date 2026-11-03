import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path

import eml_inspect as tool


SCRIPT = Path(__file__).with_name("eml_inspect.py")


class EmlInspectTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )

    def test_headers_report_names_not_values(self):
        result = tool.inspect_message(b"From: private@example.test\nSubject: secret\n\nbody")
        encoded = json.dumps(result)
        self.assertEqual([x["name"] for x in result["headers"]], ["From", "Subject"])
        self.assertNotIn("private@example", encoded)
        self.assertNotIn("secret", encoded)

    def test_duplicate_headers_are_counted_case_insensitively(self):
        result = tool.inspect_message(b"Received: one\nreceived: two\n\nbody")
        self.assertEqual(result["headers"], [{"name": "Received", "count": 2}])

    def test_plain_body_size_and_digest(self):
        result = tool.inspect_message(b"Content-Type: text/plain\n\nhello")
        part = result["parts"][0]
        self.assertEqual(part["decoded_size"], 5)
        self.assertEqual(part["sha256"], hashlib.sha256(b"hello").hexdigest())

    def test_base64_payload_is_decoded(self):
        message = b"Content-Type: application/octet-stream\nContent-Transfer-Encoding: base64\n\naGVsbG8=\n"
        result = tool.inspect_message(message)
        self.assertEqual(result["parts"][0]["decoded_size"], 5)

    def test_multipart_counts_leaf_parts(self):
        message = (
            b"Content-Type: multipart/mixed; boundary=x\n\n"
            b"--x\nContent-Type: text/plain\n\none\n"
            b"--x\nContent-Type: text/html\n\n<b>two</b>\n--x--\n"
        )
        result = tool.inspect_message(message)
        self.assertTrue(result["multipart"])
        self.assertEqual(result["leaf_part_count"], 2)

    def test_attachment_metadata(self):
        message = (
            b"Content-Type: multipart/mixed; boundary=x\n\n"
            b"--x\nContent-Disposition: attachment; filename=report.txt\n\nfile\n--x--\n"
        )
        result = tool.inspect_message(message)
        self.assertEqual(result["attachment_count"], 1)
        self.assertEqual(result["parts"][0]["filename"], "report.txt")

    def test_inline_filename_counts_as_attachment(self):
        message = b"Content-Disposition: inline; filename=image.png\n\ndata"
        self.assertEqual(tool.inspect_message(message)["attachment_count"], 1)

    def test_binary_payload_digest(self):
        message = b"Content-Transfer-Encoding: base64\n\nAP8Q\n"
        result = tool.inspect_message(message)
        self.assertEqual(result["parts"][0]["sha256"], hashlib.sha256(b"\x00\xff\x10").hexdigest())

    def test_surrogate_escaped_payload_recovers_original_byte(self):
        part = EmailMessage()
        part.set_payload("\udcff")
        self.assertEqual(tool.payload_bytes(part), b"\xff")

    def test_empty_message_is_a_zero_byte_leaf(self):
        result = tool.inspect_message(b"")
        self.assertEqual(result["leaf_part_count"], 1)
        self.assertEqual(result["parts"][0]["decoded_size"], 0)

    def test_malformed_boundary_reports_defect(self):
        result = tool.inspect_message(b"Content-Type: multipart/mixed; boundary=x\n\nno boundary")
        names = {item["name"] for item in result["defects"]}
        self.assertIn("StartBoundaryNotFoundDefect", names)

    def test_text_render_does_not_include_body(self):
        result = tool.inspect_message(b"Subject: private subject\n\nprivate body")
        rendered = tool.render_text(result)
        self.assertNotIn("private subject", rendered)
        self.assertNotIn("private body", rendered)

    def test_cli_reads_stdin_json(self):
        result = self.run_cli("-", data=b"From: a@example.test\n\nhello")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["header_count"], 1)

    def test_cli_reads_file_as_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "message.eml"
            path.write_bytes(b"Content-Type: text/plain\n\nhello")
            result = self.run_cli(str(path), "--text")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"Leaf parts: 1", result.stdout)

    def test_cli_missing_file(self):
        result = self.run_cli("missing-message.eml")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"error:", result.stderr)

    def test_crlf_message(self):
        result = tool.inspect_message(b"From: a@example.test\r\n\r\nbody\r\n")
        self.assertEqual(result["parts"][0]["decoded_size"], 6)


if __name__ == "__main__":
    unittest.main()
