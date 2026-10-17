![A realistic cat and fish playing mahjong beneath the title Hugo's Daily Tools](assets/dailytools-thumbnail.jpg)

# Hugo's Daily Tools

**Small tools. Real problems. A slightly questionable mahjong team.**

A growing collection of practical utilities by [Hugo Syarof](https://github.com/HugoIrfenz). Developer helpers, text and data converters, and file utilities — each focused on doing one useful thing well.

## Browse the tools

| Tool | What it does | Runtime |
| --- | --- | --- |
| [JSON Diff](tools/json-diff/README.md) | Compare API responses or JSON files with precise field-level changes | Python 3.9+, no dependencies |
| [Env Audit](tools/env-audit/README.md) | Check dotenv files for missing, undocumented, duplicate, empty, or malformed keys without exposing values | Python 3.9+, no dependencies |
| [Duplicate Finder](tools/duplicate-finder/README.md) | Find byte-identical files safely and estimate reclaimable space without deleting anything | Python 3.9+, no dependencies |
| [JSONL Check](tools/jsonl-check/README.md) | Validate JSON Lines with line-level errors, duplicate-key checks, and bounded error details | Python 3.9+, no dependencies |
| [CSV Audit](tools/csv-audit/README.md) | Check CSV headers, quoting, encoding, and row widths without exposing field contents | Python 3.9+, no dependencies |
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
