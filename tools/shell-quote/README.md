# Shell Quote

Quote arguments as a POSIX shell command line using Python's shlex module. Requires Python 3.9+ with no third-party packages.

```bash
python tools/shell-quote/shell_quote.py -- echo 'hello world' ''
```

This prints `echo 'hello world' ''`. The tool outputs text and does not execute commands. Quoting targets POSIX shells and does not support Windows cmd.exe or PowerShell syntax.
