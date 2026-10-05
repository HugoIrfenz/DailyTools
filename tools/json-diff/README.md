# JSON Diff

Compare expected and actual API responses without uploading them anywhere. Reports added, removed, and changed values using JSON Pointer paths.

## Requirements

- Python 3.9 or newer (`python3`, `python`, or `py -3`, depending on your system).
- Standard library only. No installation, account, or network access required.

Run the following commands from the repository root.

## Quick start

```bash
python tools/json-diff/json_diff.py tools/json-diff/examples/before.json tools/json-diff/examples/after.json
```

Expected output (the command exits with status **1**, meaning differences were found):

```text
3 difference(s):
ADD "/request_id": "demo-002"
REPLACE "/user/active": false -> true
REPLACE "/user/roles/1": "viewer" -> "editor"
```

Compare your own saved responses:

```bash
python tools/json-diff/json_diff.py expected.json actual.json
```

For a machine-readable report:

```bash
python tools/json-diff/json_diff.py expected.json actual.json --json
```

The report contains `equal`, `count`, and `changes`. Each change contains `op` and `path`, plus `before`, `after`, or both as appropriate. Example:

```json
{"equal":false,"count":1,"changes":[{"op":"replace","path":"/status","before":"pending","after":"ready"}]}
```

Read one document from stdin (shell example for macOS/Linux):

```bash
cat actual.json | python tools/json-diff/json_diff.py expected.json - --json
```

Only one argument may be `-`. Files are read as UTF-8; a leading UTF-8 BOM is accepted. Inputs are never modified and no files are created by the tool. Output goes to stdout; errors go to stderr. The report includes input values, so choose its destination appropriately.

## Comparison rules

| Case | Behavior |
| --- | --- |
| Object key order | Ignored; reported paths are sorted by key |
| Arrays | Compared by position; reordered items are differences |
| Numbers | Exact decimal comparison; `1` equals `1.0` |
| Booleans | `true` differs from `1`, and `false` differs from `0` |
| Missing versus null | A missing key differs from an explicit `null` |
| Root replacement | Uses the empty pointer `""` |
| Special key characters | `~` becomes `~0`, `/` becomes `~1` in paths |
| Duplicate object keys | Rejected, avoiding silently discarded values |
| `NaN` / `Infinity` | Rejected as non-standard JSON |

## Exit codes

- **0:** documents are equal.
- **1:** at least one difference was found. This is a comparison result, not an execution failure.
- **2:** invalid JSON, unreadable file, unsupported encoding, excessive nesting, or invalid arguments.

## Limitations

Documents are loaded into memory. This is intended for reasonably sized response/config files, not enormous datasets. Deeply nested documents and extremely long numeric literals are subject to Python's parser/runtime limits. No field-ignore rules, schema validation, fuzzy array matching, or Unicode normalization are applied. The output is a change report **not an executable JSON Patch**; in particular, array removal order is not designed for patch application. JSON is emitted on one line and preserves decimal precision.

## Verification

```bash
python -m unittest discover -s tools/json-diff -v
```

The suite covers object ordering, nested additions/removals/replacements, missing versus null, pointer escaping and Unicode, root changes, boolean/number distinctions, arrays, exact decimals, duplicate keys and malformed inputs, stdin/BOM handling, control-character-safe output, JSON reports, and exit codes.
