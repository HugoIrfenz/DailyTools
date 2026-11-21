# JSON String Codec

Encode UTF-8 text as one JSON string, or decode one JSON string into UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf 'hello\n' | python tools/json-string-codec/json_string_codec.py encode -
python tools/json-string-codec/json_string_codec.py decode quoted.json > plain.txt
```

The example prints `"hello\n"`. Output has no added newline. Encoding uses ASCII JSON escapes. Decoding rejects non-string JSON values and strings that cannot be encoded as UTF-8. The full input is held in memory.
