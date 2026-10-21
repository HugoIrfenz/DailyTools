import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jwt_inspect import MAX_INPUT, decode_segment, inspect_token, read_limited

SCRIPT = Path(__file__).with_name("jwt_inspect.py")


def segment(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def token(header='{"alg":"HS256","typ":"JWT"}', payload='{"sub":"123","admin":true}', signature=b"sig"):
    return b".".join((segment(header), segment(payload), segment(signature)))


class JwtTests(unittest.TestCase):
    def test_valid_token(self):
        result = inspect_token(token())
        self.assertEqual(result["header"], {"alg": "HS256", "typ": "JWT"})
        self.assertEqual(result["payload"], {"sub": "123", "admin": True})
        self.assertEqual((result["signature_bytes"], result["signature_present"]), (3, True))

    def test_unicode_and_exact_json_values(self):
        result = inspect_token(token('{"kid":"猫"}', '{"name":"🌼","items":[1,null,false]}'))
        self.assertEqual(result["header"]["kid"], "猫")
        self.assertEqual(result["payload"]["name"], "🌼")

    def test_empty_signature_is_reported(self):
        data = segment(b'{"alg":"none"}') + b"." + segment(b'{"sub":"1"}') + b"."
        result = inspect_token(data)
        self.assertEqual((result["signature_bytes"], result["signature_present"]), (0, False))

    def test_outer_ascii_whitespace_only(self):
        self.assertEqual(inspect_token(b" \t\r\n" + token() + b"\n")["payload"]["sub"], "123")
        with self.assertRaises(ValueError):
            inspect_token(token() + b" \v")

    def test_segment_count_and_required_segments(self):
        for data in [b"", b"a", b"a.b", b"a.b.c.d", b".e30.", b"e30.."]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                inspect_token(data)

    def test_invalid_alphabet_and_padding(self):
        for bad in [b"e30=", b"e30+", b"e30/", b"e30\n", b"e30 "]:
            data = bad + b"." + segment(b"{}") + b"." + segment(b"s")
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                inspect_token(data)

    def test_reject_noncanonical_unused_bits(self):
        self.assertEqual(decode_segment(b"Zg", "test"), b"f")
        for value in [b"Zh", b"Zm9"]:
            with self.assertRaises(ValueError):
                decode_segment(value, "test")

    def test_json_must_be_utf8_objects(self):
        cases = [(b"\xff", b"{}"), (b"[]", b"{}"), (b"{}", b"null"),
                 (b'{"x":1} trailing', b"{}")]
        for header, payload in cases:
            data = b".".join((segment(header), segment(payload), segment(b"s")))
            with self.subTest(header=header, payload=payload), self.assertRaises(ValueError):
                inspect_token(data)

    def test_duplicate_keys_at_any_depth_rejected(self):
        for value in ['{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}']:
            with self.assertRaises(ValueError):
                inspect_token(token(payload=value))

    def test_nonfinite_json_numbers_rejected(self):
        for value in ['{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e400}']:
            with self.assertRaises(ValueError):
                inspect_token(token(payload=value))

    def test_input_limit(self):
        self.assertEqual(len(read_limited(io.BytesIO(b"a" * MAX_INPUT))), MAX_INPUT)
        with self.assertRaises(ValueError):
            read_limited(io.BytesIO(b"a" * (MAX_INPUT + 1)))

    def test_cli_stdin_compact_and_pretty(self):
        raw = token()
        compact = subprocess.run([sys.executable, str(SCRIPT)], input=raw, capture_output=True)
        self.assertEqual(compact.returncode, 0)
        self.assertNotIn(b"\n  ", compact.stdout)
        self.assertEqual(json.loads(compact.stdout)["payload"]["sub"], "123")
        pretty = subprocess.run([sys.executable, str(SCRIPT), "--pretty"], input=raw, capture_output=True)
        self.assertEqual(pretty.returncode, 0)
        self.assertIn(b'\n  "header"', pretty.stdout)

    def test_cli_file_not_modified(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "token.txt"
            raw = token()
            path.write_bytes(raw)
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True)
            self.assertEqual(run.returncode, 0)
            self.assertEqual(path.read_bytes(), raw)

    def test_cli_error_has_no_token_or_stdout(self):
        private = b"PRIVATE-CONTENT"
        run = subprocess.run([sys.executable, str(SCRIPT)], input=private, capture_output=True)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, b"")
        self.assertNotIn(private, run.stderr)


if __name__ == "__main__":
    unittest.main()
