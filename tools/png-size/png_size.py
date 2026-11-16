"""Read image dimensions from a local PNG header."""
import argparse
import struct
import zlib
from pathlib import Path


def dimensions(source):
    header = source.read(33)
    if len(header) != 33 or header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        raise ValueError("missing PNG signature or complete IHDR chunk")
    width, height = struct.unpack(">II", header[16:24])
    checksum, = struct.unpack(">I", header[29:33])
    if zlib.crc32(header[12:29]) != checksum:
        raise ValueError("IHDR checksum mismatch")
    if not (0 < width < 2**31 and 0 < height < 2**31):
        raise ValueError("dimensions outside PNG bounds")
    return width, height


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        with args.file.open("rb") as source:
            width, height = dimensions(source)
    except (OSError, ValueError) as error:
        parser.exit(1, f"png-size: {error}\n")
    print(f"{width}x{height}")


if __name__ == "__main__":
    main()
