# Unix Mode

Convert Unix permission bits between octal and nine-character symbolic forms. Setuid, setgid, and sticky bits are included.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/unix-mode/unix_mode.py 755 4755
python tools/unix-mode/unix_mode.py rwxr-xr-- --json
```

Examples:

```text
755: 0755 rwxr-xr-x
4755: 4755 rwsr-xr-x
```

Accepted octal input contains three or four permission digits, with one optional leading zero. Symbolic input must contain exactly nine permission characters. The command only converts permission bits; it does not read or change files, include the file-type character from `ls -l`, or report ACLs and extended attributes.

Run the tests:

```bash
python -m unittest discover -s tools/unix-mode -p 'test_*.py'
```
