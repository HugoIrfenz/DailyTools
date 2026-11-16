# PNG Size

Print the pixel dimensions of a local PNG as `WIDTHxHEIGHT`. Requires Python 3.9+ with no third-party packages.

```bash
python tools/png-size/png_size.py screenshot.png
```

For a 640 by 480 image this prints `640x480`. The tool checks the PNG signature, IHDR checksum, and dimension bounds. It reads the first 33 bytes only and does not validate image data or later chunks.
