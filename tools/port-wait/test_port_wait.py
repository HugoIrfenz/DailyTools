import json
from pathlib import Path
import socket
import subprocess
import sys
import unittest

import port_wait as tool


SCRIPT = Path(__file__).with_name("port_wait.py")


class FakeTime:
    def __init__(self):
        self.value = 0.0
        self.sleeps = []

    def clock(self):
        return self.value

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.value += duration


class SequenceConnector:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.timeouts = []

    def __call__(self, host, port, timeout):
        self.timeouts.append(timeout)
        return next(self.outcomes, False)


class PortWaitTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def test_immediate_success(self):
        fake = FakeTime()
        report = tool.wait_for_port("db", 5432, connector=SequenceConnector([True]),
                                    clock=fake.clock, sleeper=fake.sleep)
        self.assertTrue(report["ok"])
        self.assertEqual(report["attempts"], 1)
        self.assertEqual(fake.sleeps, [])

    def test_retries_until_success(self):
        fake = FakeTime()
        report = tool.wait_for_port("db", 5432, timeout=2, interval=.2,
                                    connector=SequenceConnector([False, False, True]),
                                    clock=fake.clock, sleeper=fake.sleep)
        self.assertTrue(report["ok"])
        self.assertEqual(report["attempts"], 3)
        self.assertEqual(report["elapsed_seconds"], .4)

    def test_stability_streak_resets_after_failure(self):
        fake = FakeTime()
        connector = SequenceConnector([True, False, True, True])
        report = tool.wait_for_port("cache", 6379, timeout=2, interval=.1,
                                    stable=2, connector=connector,
                                    clock=fake.clock, sleeper=fake.sleep)
        self.assertTrue(report["ok"])
        self.assertEqual(report["attempts"], 4)
        self.assertEqual(report["consecutive_successes"], 2)

    def test_timeout_keeps_last_streak_and_clamps_sleep(self):
        fake = FakeTime()
        connector = SequenceConnector([False, True, False, False])
        report = tool.wait_for_port("api", 8080, timeout=.5, interval=.2,
                                    stable=2, connector=connector,
                                    clock=fake.clock, sleeper=fake.sleep)
        self.assertFalse(report["ok"])
        self.assertEqual(report["attempts"], 4)
        self.assertEqual(report["consecutive_successes"], 0)
        self.assertAlmostEqual(sum(fake.sleeps), .5)

    def test_zero_timeout_performs_exactly_one_probe(self):
        fake = FakeTime()
        connector = SequenceConnector([False, True])
        report = tool.wait_for_port("api", 80, timeout=0, connector=connector,
                                    clock=fake.clock, sleeper=fake.sleep)
        self.assertFalse(report["ok"])
        self.assertEqual(report["attempts"], 1)
        self.assertEqual(fake.sleeps, [])

    def test_connect_timeout_is_limited_by_remaining_time(self):
        fake = FakeTime()
        connector = SequenceConnector([False, False])
        tool.wait_for_port("api", 80, timeout=.1, interval=.1, connect_timeout=5,
                           connector=connector, clock=fake.clock, sleeper=fake.sleep)
        self.assertEqual(connector.timeouts, [.1, .001])

    def test_endpoint_formats_ipv4_names_and_ipv6(self):
        self.assertEqual(tool.endpoint("localhost", 80), "localhost:80")
        self.assertEqual(tool.endpoint("127.0.0.1", 80), "127.0.0.1:80")
        self.assertEqual(tool.endpoint("::1", 80), "[::1]:80")
        self.assertEqual(tool.host_value("[::1]"), "::1")

    def test_argument_validators(self):
        for value in ("0", "65536", "text"):
            with self.subTest(port=value), self.assertRaises(Exception):
                tool.port_value(value)
        for value in ("", " bad", "bad\nname"):
            with self.subTest(host=value), self.assertRaises(Exception):
                tool.host_value(value)
        for value in ("nan", "inf", "-1"):
            with self.subTest(duration=value), self.assertRaises(Exception):
                tool.duration_value(value, True)

    def test_cli_succeeds_against_local_listener_text_and_json(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(listener.close)
        listener.bind(("127.0.0.1", 0))
        listener.listen(5)
        port = listener.getsockname()[1]
        text = self.cli("127.0.0.1", port, "--timeout", ".5", "--stable", "2")
        self.assertEqual(text.returncode, 0)
        self.assertIn("READY: 127.0.0.1", text.stdout)
        structured = self.cli("127.0.0.1", port, "--timeout", ".5", "--json")
        self.assertEqual(structured.returncode, 0)
        self.assertTrue(json.loads(structured.stdout)["ok"])

    def test_cli_closed_local_port_times_out(self):
        temporary = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temporary.bind(("127.0.0.1", 0))
        port = temporary.getsockname()[1]
        temporary.close()
        result = self.cli("127.0.0.1", port, "--timeout", ".05",
                          "--interval", ".01", "--json")
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report["ok"])
        self.assertGreaterEqual(report["attempts"], 1)

    def test_cli_bad_arguments_exit_two(self):
        cases = [
            ("host", "0"), ("host", "80", "--timeout", "-1"),
            ("host", "80", "--interval", "0"),
            ("host", "80", "--connect-timeout", "nan"),
            ("host", "80", "--stable", "101"),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
