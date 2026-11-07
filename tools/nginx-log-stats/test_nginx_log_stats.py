import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from nginx_log_stats import LogError, parse_line, summarize

SCRIPT = Path(__file__).with_name("nginx_log_stats.py")

def log(request='GET / HTTP/1.1', status='200', size='123', extra=''):
    return f'192.0.2.1 - - [07/Nov/2026:10:00:00 +0000] "{request}" {status} {size}{extra}'

class NginxLogStatsTests(unittest.TestCase):
    def test_parse_common_log_line(self):
        self.assertEqual(parse_line(log()), ("GET", "/", "200", 123, True))
    def test_parse_combined_log_line(self):
        line = log(extra=' "https://example.test/" "agent"')
        self.assertEqual(parse_line(line), ("GET", "/", "200", 123, True))
        self.assertEqual(summarize(line)["bytes_known_lines"], 1)
    def test_query_string_is_not_in_path_aggregate(self):
        self.assertEqual(parse_line(log("GET /search?q=secret HTTP/1.1"))[1], "/search")
    def test_absolute_request_target(self):
        self.assertEqual(parse_line(log("GET https://example.test/a?b=1 HTTP/1.1"))[1], "/a")
    def test_connect_target(self):
        self.assertEqual(parse_line(log("CONNECT example.test:443 HTTP/1.1"))[1], "example.test:443")
    def test_asterisk_target(self):
        self.assertEqual(parse_line(log("OPTIONS * HTTP/1.1"))[1], "*")
    def test_dash_request_and_unknown_size(self):
        self.assertEqual(parse_line(log("-", "-", "-")), ("UNKNOWN", "UNKNOWN", "-", 0, False))
    def test_malformed_line_returns_none(self):
        self.assertIsNone(parse_line("not an access log"))
    def test_malformed_request_is_rejected(self):
        self.assertIsNone(parse_line(log("GET /")))
    def test_escaped_quote_in_request(self):
        parsed = parse_line(log(r'GET /a\\"b HTTP/1.1'))
        self.assertEqual(parsed[0], "GET")
    def test_summary_counts_methods_status_and_bytes(self):
        source = "\\n".join([log("GET /a HTTP/1.1", "200", "10"), log("POST /b HTTP/1.1", "404", "20"), log("GET /a HTTP/1.1", "500", "-")])
        result = summarize(source)
        self.assertEqual(result["parsed"], 3)
        self.assertEqual(result["client_errors"], 1)
        self.assertEqual(result["server_errors"], 1)
        self.assertEqual(result["total_bytes"], 30)
        self.assertEqual(result["bytes_known_lines"], 2)
        self.assertEqual(result["method_counts"], {"GET": 2, "POST": 1})
    def test_malformed_lines_are_counted(self):
        result = summarize(log() + "\\ninvalid\\n")
        self.assertEqual(result["lines"], 2)
        self.assertEqual(result["malformed"], 1)
    def test_blank_lines_are_ignored(self):
        self.assertEqual(summarize("\\n" + log() + "\\n\\n")["lines"], 1)
    def test_top_paths_are_ranked_deterministically(self):
        source = "\\n".join([log("GET /b HTTP/1.1"), log("GET /a HTTP/1.1"), log("GET /b HTTP/1.1")])
        self.assertEqual(summarize(source)["top_paths"], [{"value": "/b", "count": 2}, {"value": "/a", "count": 1}])
    def test_top_limit(self):
        source = "\\n".join(log(f"GET /{n} HTTP/1.1") for n in range(4))
        self.assertEqual(len(summarize(source, top=2)["top_paths"]), 2)
    def test_paths_can_be_omitted(self):
        result = summarize(log(), include_paths=False)
        self.assertEqual(result["top_paths"], [])
    def test_invalid_top_is_rejected(self):
        with self.assertRaisesRegex(LogError, "at least 1"):
            summarize(log(), top=0)
    def test_cli_stdin_json(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--json"], input=log() + "\\n", text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["parsed"], 1)
    def test_cli_no_paths(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--json", "--no-paths"], input=log() + "\\n", text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout)["top_paths"], [])
    def test_cli_reads_utf8_bom_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "access.log")
            path.write_bytes(("\\ufeff" + log() + "\\n").encode("utf-8"))
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--json"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["parsed"], 1)
    def test_cli_invalid_top_exit_code(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--top", "0"], input=log() + "\\n", text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("at least 1", result.stderr)

if __name__ == "__main__":
    unittest.main()
