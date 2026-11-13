import argparse
import sys
from pathlib import Path


def copy_slice(source, output, offset, length):
    source.seek(offset)
    remaining = length
    while remaining:
        chunk = source.read(min(remaining, 65536))
        if not chunk:
            break
        output.write(chunk)
        remaining -= len(chunk)


def main():
    parser = argparse.ArgumentParser(description="Copy a byte range from a seekable file.")
    parser.add_argument("file", type=Path)
    parser.add_argument("offset", type=int)
    parser.add_argument("length", type=int)
    args = parser.parse_args()
    if args.offset < 0 or args.length < 0:
        parser.error("offset and length must be nonnegative")
    try:
        with args.file.open("rb") as source:
            copy_slice(source, sys.stdout.buffer, args.offset, args.length)
        sys.stdout.buffer.flush()
    except (OSError, OverflowError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
