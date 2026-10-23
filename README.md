![A realistic cat and fish playing mahjong beneath the title Hugo's Daily Tools](assets/dailytools-thumbnail.jpg)

# Hugo's Daily Tools

**Small tools. Real problems. A slightly questionable mahjong team.**

A growing collection of practical utilities by [Hugo Syarof](https://github.com/HugoIrfenz). Developer helpers, text and data converters, and file utilities — each focused on doing one useful thing well.

## Browse the tools

| Tool | What it does | Runtime |
| --- | --- | --- |
| [JSON Diff](tools/json-diff/README.md) | Compare API responses or JSON files with precise field-level changes | Python 3.9+, no dependencies |
| [JSON Merge Patch](tools/json-merge-patch/README.md) | Apply object updates, removals, and replacements from a merge-patch document | Python 3.9+, no dependencies |
| [Env Audit](tools/env-audit/README.md) | Check dotenv files for missing, undocumented, duplicate, empty, or malformed keys without exposing values | Python 3.9+, no dependencies |
| [Duplicate Finder](tools/duplicate-finder/README.md) | Find byte-identical files safely and estimate reclaimable space without deleting anything | Python 3.9+, no dependencies |
| [JSONL Check](tools/jsonl-check/README.md) | Validate JSON Lines with line-level errors, duplicate-key checks, and bounded error details | Python 3.9+, no dependencies |
| [CSV Audit](tools/csv-audit/README.md) | Check CSV headers, quoting, encoding, and row widths without exposing field contents | Python 3.9+, no dependencies |
| [CSV Select](tools/csv-select/README.md) | Select and reorder CSV columns with header and row-width validation | Python 3.9+, no dependencies |
| [Cron Next](tools/cron-next/README.md) | Validate five-field cron expressions and preview timezone-aware run times | Python 3.9+, no dependencies |
| [Hash Manifest](tools/hash-manifest/README.md) | Create and verify deterministic SHA-256 inventories without following symlinks | Python 3.9+, no dependencies |
| [Port Wait](tools/port-wait/README.md) | Wait for a TCP endpoint with retries, timeout, stability checks, and JSON output | Python 3.9+, no dependencies |
| [Line Unique](tools/line-unique/README.md) | Remove duplicate text lines while retaining first-seen order | Python 3.9+, no dependencies |
| [Subnet Inspect](tools/subnet-inspect/README.md) | Inspect IPv4/IPv6 CIDRs and check address membership | Python 3.9+, no dependencies |
| [Query Decode](tools/query-decode/README.md) | Decode form query strings into ordered name/value pairs | Python 3.10+, no dependencies |
| [EOL Inspect](tools/eol-inspect/README.md) | Count LF, CRLF and CR endings and check final newlines | Python 3.9+, no dependencies |
| [Epoch Convert](tools/epoch-convert/README.md) | Convert Unix timestamps and offset-aware ISO datetimes | Python 3.9+, no dependencies |
| [Path Collisions](tools/path-collisions/README.md) | Find Unicode-normalized and case-insensitive path collisions | Python 3.9+, no dependencies |
| [JSON Select](tools/json-select/README.md) | Extract JSON values using explicit keys and array indexes | Python 3.9+, no dependencies |
| [Tree Usage](tools/tree-usage/README.md) | Summarize file counts and logical bytes by final extension | Python 3.9+, no dependencies |
| [File Compare](tools/file-compare/README.md) | Compare files and report the first differing byte offset | Python 3.9+, no dependencies |
| [Duration Sum](tools/duration-sum/README.md) | Add signed durations with integer microsecond precision | Python 3.9+, no dependencies |
| [Base64 Codec](tools/base64-codec/README.md) | Encode bytes or validate and decode padded Base64 | Python 3.9+, no dependencies |
| [ZIP Inventory](tools/zip-inventory/README.md) | Summarize ZIP entry sizes, duplicate names and largest files without extraction | Python 3.9+, no dependencies |
| [Retry Command](tools/retry-command/README.md) | Retry local commands after nonzero exits or per-attempt timeouts | Python 3.9+, no dependencies |
| [Text Transcode](tools/text-transcode/README.md) | Convert explicit text encodings with strict errors and binary stdout | Python 3.9+, no dependencies |
| [Byte Size](tools/byte-size/README.md) | Parse exact byte quantities and display decimal and binary sizes | Python 3.9+, no dependencies |
| [List Compare](tools/list-compare/README.md) | Compare UTF-8 line-list membership in first-seen order | Python 3.9+, no dependencies |
| [Unicode Inspect](tools/unicode-inspect/README.md) | Locate selected Unicode control, format and separator characters | Python 3.9+, no dependencies |
| [JWT Inspect](tools/jwt-inspect/README.md) | Decode compact token JSON without verifying its signature | Python 3.9+, no dependencies |
| [UUID Inspect](tools/uuid-inspect/README.md) | Normalize UUID text and report its encoded version, variant, and forms | Python 3.9+, no dependencies |
| [SemVer Compare](tools/semver-compare/README.md) | Compare Semantic Versions with prerelease precedence and ignored build metadata | Python 3.9+, no dependencies |

## Getting started

Clone the repository:

```bash
git clone https://github.com/HugoIrfenz/DailyTools.git
cd DailyTools
```

Pick a tool from the catalog and follow its README. There is no global installation step: each utility documents its own runtime, dependencies, commands, examples, and limitations.

## Structure

```text
DailyTools/
├── README.md
├── assets/
│   └── dailytools-thumbnail.jpg
└── tools/
    ├── semver-compare/
    │   ├── README.md
    │   ├── semver_compare.py
    │   └── test_semver_compare.py
    ├── json-merge-patch/
    │   ├── README.md
    │   ├── json_merge_patch.py
    │   └── test_json_merge_patch.py
    ├── uuid-inspect/
    │   ├── README.md
    │   ├── uuid_inspect.py
    │   └── test_uuid_inspect.py
    ├── csv-select/
    │   ├── README.md
    │   ├── csv_select.py
    │   └── test_csv_select.py
    ├── jwt-inspect/
    │   ├── README.md
    │   ├── jwt_inspect.py
    │   └── test_jwt_inspect.py
    ├── unicode-inspect/
    │   ├── README.md
    │   ├── unicode_inspect.py
    │   └── test_unicode_inspect.py
    ├── list-compare/
    │   ├── README.md
    │   ├── list_compare.py
    │   └── test_list_compare.py
    ├── byte-size/
    │   ├── README.md
    │   ├── byte_size.py
    │   └── test_byte_size.py
    ├── text-transcode/
    │   ├── README.md
    │   ├── text_transcode.py
    │   └── test_text_transcode.py
    ├── retry-command/
    │   ├── README.md
    │   ├── retry_command.py
    │   └── test_retry_command.py
    ├── zip-inventory/
    │   ├── README.md
    │   ├── zip_inventory.py
    │   └── test_zip_inventory.py
    ├── base64-codec/
    │   ├── README.md
    │   ├── base64_codec.py
    │   └── test_base64_codec.py
    ├── duration-sum/
    │   ├── README.md
    │   ├── duration_sum.py
    │   └── test_duration_sum.py
    ├── file-compare/
    │   ├── README.md
    │   ├── file_compare.py
    │   └── test_file_compare.py
    ├── tree-usage/
    │   ├── README.md
    │   └── ...source files
    ├── json-select/
    │   ├── README.md
    │   └── ...source files
    ├── path-collisions/
    │   ├── README.md
    │   └── ...source files
    ├── epoch-convert/
    │   ├── README.md
    │   └── ...source files
    ├── eol-inspect/
    │   ├── README.md
    │   └── ...source files
    ├── query-decode/
    │   ├── README.md
    │   └── ...source files
    ├── cron-next/
    │   ├── README.md
    │   └── ...source files
    ├── csv-audit/
    │   ├── README.md
    │   └── ...source files
    ├── duplicate-finder/
    │   ├── README.md
    │   └── ...source files
    ├── env-audit/
    │   ├── README.md
    │   └── ...source files
    ├── hash-manifest/
    │   ├── README.md
    │   └── ...source files
    ├── json-diff/
    │   ├── README.md
    │   └── ...source files
    ├── jsonl-check/
    │   ├── README.md
    │   └── ...source files
    ├── line-unique/
    │   ├── README.md
    │   └── ...source files
    ├── port-wait/
    │   ├── README.md
    │   └── ...source files
    └── subnet-inspect/
        ├── README.md
        └── ...source files
```

## How this collection grows

New utilities are selected and built through a daily automation scheduled for **12:00 WIB (Asia/Jakarta)**. Each run is tasked with inspecting the existing collection, choosing a useful idea, checking its behavior, and publishing the code together with documentation. Failed runs are reported rather than treated as successful releases.

## Quality bar

- **Useful:** solve a concrete problem; no empty activity commits.
- **Simple:** keep setup understandable and dependencies minimal.
- **Verified:** check normal usage and relevant edge cases before release.
- **Documented:** include copyable commands, examples, and honest limitations.
- **Local when practical:** explain any network access or external service requirements.
- **Careful with files:** document side effects and preserve unrelated work.

## Ideas and contributions

Open an [issue](https://github.com/HugoIrfenz/DailyTools/issues) with the problem you want to solve, an example input, and the desired output. Improvements to existing tools are welcome through pull requests.

## Cover

The AI-generated cover features a realistic cat and fish playing mahjong. Created for this repository; the artwork is stored in [assets/dailytools-thumbnail.jpg](assets/dailytools-thumbnail.jpg).

---

Built by **Hugo Syarof**, with Angela helping turn little ideas into working tools.
