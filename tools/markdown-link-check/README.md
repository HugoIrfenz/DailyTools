# Markdown Link Check

Check whether relative file targets in Markdown links exist. It accepts one Markdown file, recursively scans a directory for `.md` files, or reads Markdown from standard input. Inline links, images, and reference definitions are recognized; external URLs, anchors, and root-relative site paths are skipped.

Requires Python 3.9 or newer and has no dependencies.

```bash
python tools/markdown-link-check/markdown_link_check.py README.md
python tools/markdown-link-check/markdown_link_check.py docs/ --json
cat README.md | python tools/markdown-link-check/markdown_link_check.py - --base .
```

Exit status is 0 when all checked targets exist, 1 when any are missing, and 2 for input errors. Fragments are not validated. The parser handles common inline and reference-definition syntax but is not a complete CommonMark parser; nested brackets, unusually nested parentheses, generated links, and HTML links may not be recognized.
