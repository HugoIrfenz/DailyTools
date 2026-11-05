# Markdown TOC

Generate a Markdown table of contents from ATX headings (`#` through `######`). Headings inside backtick or tilde fenced code blocks are ignored. Duplicate anchors receive numeric suffixes.

Requires Python 3.9 or newer. It uses only the standard library.

```bash
python tools/markdown-toc/markdown_toc.py README.md
cat README.md | python tools/markdown-toc/markdown_toc.py
python tools/markdown-toc/markdown_toc.py --min-level 1 --max-level 3 README.md
```

The default range is H2 through H6. For this input:

```markdown
# Project
## Install
### Linux
## Install
```

the output is:

```markdown
- [Install](#install)
  - [Linux](#linux)
- [Install](#install-1)
```

Anchor generation is local and deterministic: text is case-folded, punctuation is removed, and runs of whitespace or hyphens become one hyphen. It does not reproduce every renderer's anchor rules. Setext headings, HTML headings, explicit heading IDs, and inline Markdown normalization are not supported. The complete input is read into memory.

Run the tests with:

```bash
python -m unittest discover -s tools/markdown-toc -p 'test_*.py'
```
