import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from http_headers_inspect import inspect_headers

SCRIPT = Path(__file__).with_name("http_headers_inspect.py")


class InspectHeadersTests(unittest.TestCase):
    def test_response_block(self):
        result = inspect_headers(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nX-ID: 7\r\n\r\n")
        self.assertTrue(result["has_start_line"])
        self.assertEqual(result["field_count"], 2)
        self.assertEqual(result["headers"][0], {"name": "content-type", "count": 1, "value_characters": 10})

    def test_request_and_duplicates(self):
        result = inspect_headers(b"GET / HTTP/1.1\nSet-Cookie: a=1\nset-cookie: b=2")
        self.assertEqual(result["duplicate_names"], ["set-cookie"])
        self.assertEqual(result["headers"][0]["count"], 2)

    def test_headers_without_start_line(self):
        result = inspect_headers(b"Host: example.test\nAccept: */*")
        self.assertFalse(result["has_start_line"])
        self.assertEqual(result["unique_name_count"], 2)

    def test_order_and_ows(self):
        result = inspect_headers(b"X-B: \t two \t\nX-A:\nX-B:three")
        self.assertEqual([x["name"] for x in result["headers"]], ["x-b", "x-a"])
        self.assertEqual(result["total_value_characters"], 8)

    def test_unicode_value_length(self):
        result = inspect_headers("X-Name: 雪".encode())
        self.assertEqual(result["total_value_characters"], 1)

    def test_empty(self):
        self.assertEqual(inspect_headers(b"")["field_count"], 0)

    def test_bom(self):
        self.assertEqual(inspect_headers(b"\xef\xbb\xbfX-A: 1")["headers"][0]["name"], "x-a")

    def test_invalid_names(self):
        for data in (b"Bad Name: x", b": x", b"Name : x", b"N@me: x"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                inspect_headers(data)

    def test_malformed_lines(self):
        for data in (b"X-A: 1\ninvalid", b"X-A: 1\n folded", b"X-A: 1\n\tbody"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                inspect_headers(data)

    def test_rejects_body(self):
        with self.assertRaises(ValueError):
            inspect_headers(b"X-A: 1\r\n\r\nbody")

    def test_controls_and_endings(self):
        for data in (b"X-A: a\x00b", b"X-A: a\x01b", b"X-A: 1\rX-B: 2"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                inspect_headers(data)

    def test_size_limit(self):
        with self.assertRaises(ValueError):
            inspect_headers(b"x" * (1024 * 1024 + 1))

    def test_cli_json_stdin(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "-"], input=b"X-A: secret\nX-A: hidden", capture_output=True)
        parsed = json.loads(run.stdout)
        self.assertEqual((run.returncode, parsed["field_count"]), (0, 2))
        self.assertNotIn(b"secret", run.stdout)

    def test_cli_text_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "headers.txt"
            path.write_bytes(b"Host: example.test")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path), "--text"], capture_output=True)
            self.assertEqual(run.returncode, 0)
            self.assertIn(b"host\t1\t12", run.stdout)

    def test_cli_errors_without_traceback(self):
        for data in (b"Bad Name: x", b"\xff", b"X-A: a\x01b"):
            run = subprocess.run([sys.executable, str(SCRIPT), "-"], input=data, capture_output=True)
            self.assertEqual((run.returncode, run.stdout), (1, b""))
            self.assertNotIn(b"Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()
