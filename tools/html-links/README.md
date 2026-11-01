# HTML Links

Extracts common `href`, `src`, and `action` attributes from a local UTF-8 HTML document. Relative values can be resolved with `--base` or the document's first non-empty `<base href>`. Plain output contains one resolved value per line; `--json` also reports the source tag, attribute, and raw value.

Requires Python 3.9 or newer. It has no third-party dependencies and does not fetch any URL.

```bash
python tools/html-links/html_links.py page.html --base https://example.com/
cat page.html | python tools/html-links/html_links.py - --unique --json
```

The parser follows Python's tolerant HTML parsing rather than browser DOM rules. It does not extract CSS URLs, JavaScript-created links, `srcset`, meta refresh targets, or links from externally loaded content.

Run the tests with:

```bash
python -m unittest discover -s tools/html-links -p 'test_*.py'
```
