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
    ├── duplicate-finder/
    │   ├── README.md
    │   └── ...source files
    ├── env-audit/
    │   ├── README.md
    │   └── ...source files
    └── json-diff/
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
