# EML Inspect

Inventories header names and MIME leaf parts in an RFC email file without printing header values or body contents. Each leaf part reports its content type, disposition, filename, decoded size, SHA-256 digest, and parser defect names. Attachment counts include parts with an attachment disposition or filename.

Requires Python 3.9 or newer. It has no third-party dependencies and does not access a mail server or network.

```bash
python tools/eml-inspect/eml_inspect.py message.eml
cat message.eml | python tools/eml-inspect/eml_inspect.py - --text
```

Filenames are included in reports. The complete message and decoded payloads are held in memory. Python's email parser is tolerant of malformed messages, so defects are reported rather than making every malformed input fail. This tool does not verify DKIM, SPF, sender identity, links, or attachment safety.

Run the tests with:

```bash
python -m unittest discover -s tools/eml-inspect -p 'test_*.py'
```
