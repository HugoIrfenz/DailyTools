import base64
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from pem_inspect import PEMInspectError, format_text, inspect_pem


SCRIPT = Path(__file__).with_name("pem_inspect.py")


def pem(label: str, payload: bytes) -> bytes:
    encoded = base64.b64encode(payload)
    return b"-----BEGIN " + label.encode() + b"-----\n" + encoded + b"\n-----END " + label.encode() + b"-----\n"


class PEMInspectTests(unittest.TestCase):
    def test_inspects_one_block(self):
        blocks = inspect_pem(pem("CERTIFICATE", b"hello"))
        self.assertEqual(blocks[0]["label"], "CERTIFICATE")
        self.assertEqual(blocks[0]["bytes"], 5)
        self.assertEqual(blocks[0]["sha256"], hashlib.sha256(b"hello").hexdigest())

    def test_accepts_multiple_wrapped_payload_lines(self):
        data = b"-----BEGIN DATA-----\naGVs\nbG8=\n-----END DATA-----\n"
        self.assertEqual(inspect_pem(data)[0]["bytes"], 5)

    def test_accepts_blank_lines_between_blocks(self):
        blocks = inspect_pem(pem("ONE", b"a") + b"\n" + pem("TWO", b"b"))
        self.assertEqual([block["label"] for block in blocks], ["ONE", "TWO"])

    def test_marks_duplicate_payloads(self):
        blocks = inspect_pem(pem("ONE", b"same") + pem("TWO", b"same"))
        self.assertTrue(blocks[0]["duplicate_payload"])
        self.assertTrue(blocks[1]["duplicate_payload"])

    def test_unique_payload_is_not_marked_duplicate(self):
        self.assertFalse(inspect_pem(pem("ONE", b"a"))[0]["duplicate_payload"])

    def test_tracks_line_numbers(self):
        block = inspect_pem(b"\n" + pem("DATA", b"x"))[0]
        self.assertEqual((block["begin_line"], block["end_line"]), (2, 4))

    def test_rejects_mismatched_end_label(self):
        data = b"-----BEGIN ONE-----\neA==\n-----END TWO-----\n"
        with self.assertRaisesRegex(PEMInspectError, "does not match"):
            inspect_pem(data)

    def test_rejects_invalid_base64(self):
        data = b"-----BEGIN DATA-----\nnot*base64\n-----END DATA-----\n"
        with self.assertRaisesRegex(PEMInspectError, "invalid base64 line"):
            inspect_pem(data)

    def test_rejects_empty_block(self):
        data = b"-----BEGIN DATA-----\n-----END DATA-----\n"
        with self.assertRaisesRegex(PEMInspectError, "empty PEM"):
            inspect_pem(data)

    def test_rejects_unterminated_block(self):
        with self.assertRaisesRegex(PEMInspectError, "unterminated"):
            inspect_pem(b"-----BEGIN DATA-----\neA==\n")

    def test_rejects_non_pem_text(self):
        with self.assertRaisesRegex(PEMInspectError, "unexpected content"):
            inspect_pem(b"hello\n" + pem("DATA", b"x"))

    def test_rejects_no_blocks(self):
        with self.assertRaisesRegex(PEMInspectError, "no PEM"):
            inspect_pem(b"\n")

    def test_text_format_contains_digest(self):
        output = format_text(inspect_pem(pem("DATA", b"x")))
        self.assertIn("1: DATA", output)
        self.assertIn("sha256:", output)

    def test_cli_json_from_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-", "--json"],
            input=pem("DATA", b"hello"),
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)[0]["bytes"], 5)


if __name__ == "__main__":
    unittest.main()
