"""Encode or decode HTML character references in UTF-8 text."""
import argparse
import html
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("encode", "decode"))
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        text = data.decode("utf-8-sig")
        output = html.escape(text, quote=True) if args.mode == "encode" else html.unescape(text)
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"html-entities: {error}\n")


if __name__ == "__main__":
    main()
