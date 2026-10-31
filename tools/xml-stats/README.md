# XML Stats

Summarize XML structure without printing element or attribute values. It reports the root tag, element and attribute counts, decoded text-character count, maximum depth, namespace URIs, and counts for each expanded tag name.

Requires Python 3.9 or newer and uses only the standard library.

```bash
python tools/xml-stats/xml_stats.py document.xml
cat document.xml | python tools/xml-stats/xml_stats.py - --json
```

The complete input bytes and tag counter are held in memory. Comments and processing instructions are not counted as elements. Text-character counts include whitespace and decoded built-in entities. `DOCTYPE` declarations are rejected; this tool does not validate against DTD, XSD, or application-specific rules and is not an XML security scanner.
