from contextlib import redirect_stderr
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from retry_command import retry

SCRIPT = Path(__file__).with_name("retry_command.py")


def run_cli(args, timeout=10):
    return subprocess.run([sys.executable, str(SCRIPT)] + args,
                          capture_output=True, text=True, timeout=timeout)


class RetryTests(unittest.TestCase):
    def test_success_first_attempt(self):
        run = run_cli(["--delay", "0", "--", sys.executable, "-c", "print('done')"])
        self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "done\n", ""))

    def test_real_command_eventually_succeeds(self):
        with tempfile.TemporaryDirectory() as folder:
            counter = Path(folder) / "counter"
            code = ("import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
                    "n=int(p.read_text())+1 if p.exists() else 1; "
                    "p.write_text(str(n)); print(n); sys.exit(0 if n==3 else 7)")
            run = run_cli(["--attempts", "5", "--delay", "0", "--",
                           sys.executable, "-c", code, str(counter)])
            self.assertEqual(run.returncode, 0)
            self.assertEqual(run.stdout, "1\n2\n3\n")
            self.assertEqual(counter.read_text(), "3")
            self.assertEqual(run.stderr.count("exited with 7"), 2)

    def test_exhaustion_has_exact_attempt_count(self):
        run = run_cli(["--attempts", "2", "--delay", "0", "--", sys.executable,
                       "-c", "import sys; print('failed'); sys.exit(19)"])
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stdout, "failed\nfailed\n")
        self.assertIn("attempt 2/2 exited with 19", run.stderr)

    def test_child_stderr_passes_through(self):
        run = run_cli(["--", sys.executable, "-c", "import sys; print('child',file=sys.stderr)"])
        self.assertEqual(run.returncode, 0)
        self.assertEqual(run.stderr, "child\n")

    def test_arguments_are_not_shell_expanded(self):
        value = "a b; $(echo surprise) * > output"
        run = run_cli(["--", sys.executable, "-c", "import sys; print(sys.argv[1])", value])
        self.assertEqual((run.returncode, run.stdout), (0, value + "\n"))

    def test_actual_timeout_retried(self):
        run = run_cli(["--attempts", "2", "--delay", "0", "--timeout", "0.1", "--",
                       sys.executable, "-c", "import time; time.sleep(30)"])
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stderr.count("timed out"), 2)

    def test_launch_error_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            run = run_cli(["--", str(Path(folder) / "missing-executable")])
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("attempt", run.stderr)

    def test_delay_only_between_attempts(self):
        with patch("retry_command.subprocess.run", return_value=subprocess.CompletedProcess([], 1)) as command:
            with patch("retry_command.time.sleep") as sleep, redirect_stderr(io.StringIO()):
                self.assertEqual(retry(["ignored"], 3, 0.25), 1)
        self.assertEqual(command.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        sleep.assert_called_with(0.25)

    def test_cli_rejects_invalid_options(self):
        for option, values in [("--attempts", ["0", "101", "1.5"]),
                               ("--delay", ["-1", "nan", "inf", "3601"]),
                               ("--timeout", ["0", "-1", "nan", "inf", "3601"])]:
            for value in values:
                with self.subTest(option=option, value=value):
                    run = run_cli([option, value, "--", sys.executable, "-c", "print('bad')"])
                    self.assertEqual(run.returncode, 2)
                    self.assertEqual(run.stdout, "")

    def test_missing_command(self):
        for args in [[], ["--"]]:
            self.assertEqual(run_cli(args).returncode, 2)

    def test_helper_validates_before_launch(self):
        for kwargs in [{"command": []}, {"command": ["x"], "attempts": 0},
                       {"command": ["x"], "delay": float("nan")},
                       {"command": ["x"], "timeout": 0}]:
            with self.assertRaises(ValueError):
                retry(**kwargs)

    def test_interrupt_exit_code(self):
        from retry_command import main
        with patch("retry_command.retry", side_effect=KeyboardInterrupt):
            self.assertEqual(main(["--", "ignored"]), 130)


if __name__ == "__main__":
    unittest.main()
