# SemVer Compare

Compare two Semantic Version strings using major, minor, patch, and prerelease precedence. Build metadata is parsed but does not affect precedence.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/semver-compare/semver_compare.py 1.2.3 1.3.0
python tools/semver-compare/semver_compare.py 1.0.0-rc.1 1.0.0 --json
```

Text output uses `<`, `=`, or `>`. JSON output includes `result` as `-1`, `0`, or `1`. Invalid versions exit with status 1.

The parser requires the full `MAJOR.MINOR.PATCH` form. It rejects a `v` prefix and leading zeroes in numeric identifiers. Versions that differ only by build metadata compare equal, so this tool does not provide a total ordering for those strings.

Run the tests:

```bash
python -m unittest discover -s tools/semver-compare -p 'test_*.py'
```
