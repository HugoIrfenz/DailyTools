import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("shell_quote.py")

class CLITests(unittest.TestCase):
    def run_cli(self, *args, payload=b""):
        return subprocess.run([sys.executable, SCRIPT, *args], input=payload, capture_output=True)


    def test_round_trip_special_arguments(self):
        import shlex
        values = ["echo", "", "a b", "it's", "$(whoami)", "x\ny", "é"]
        result = self.run_cli("--", *values)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(shlex.split(result.stdout.decode()), values)

    def test_empty_argument_list(self):
        result = self.run_cli()
        self.assertEqual((result.returncode, result.stdout), (0, b"\n"))

