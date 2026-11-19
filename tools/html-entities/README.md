# HTML Entities

Encode or decode HTML character references in UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf '<a title="x">&</a>' | python tools/html-entities/html_entities.py encode -
python tools/html-entities/html_entities.py decode escaped.txt > decoded.txt
```

Encoding escapes ampersands, angle brackets, and quotes. Decoding follows Python's HTML5 character-reference rules. The full input is held in memory. Encoding is intended for text and quoted HTML attribute values.
