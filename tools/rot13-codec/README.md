# ROT13 Codec

Apply ROT13 to ASCII letters in UTF-8 text. Requires Python 3.9+ with no third-party packages.

```bash
printf 'Hello!' | python tools/rot13-codec/rot13_codec.py -
python tools/rot13-codec/rot13_codec.py message.txt > transformed.txt
```

The example prints `Uryyb!`. Applying ROT13 again restores the original text. Non-ASCII characters and line endings are retained. The full input is held in memory. ROT13 is reversible text obfuscation.
