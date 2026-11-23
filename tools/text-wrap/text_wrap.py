"""Wrap whitespace-separated paragraphs to a selected character width."""
import argparse
import re
import sys
import textwrap
from pathlib import Path


def wrap(text, width):
    if width < 1:
        raise ValueError("width must be positive")
    paragraphs = re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").replace("\r", "\n"))
    output = []
    for paragraph in paragraphs:
        words = " ".join(paragraph.split())
        if words:
            output.append(textwrap.fill(words, width=width, break_long_words=False,
                                        break_on_hyphens=False))
    return "\n\n".join(output) + ("\n" if output else "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    parser.add_argument("--width", type=int, default=80)
    args = parser.parse_args()
    if args.width < 1:
        parser.error("width must be positive")
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        output = wrap(data.decode("utf-8-sig"), args.width)
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"text-wrap: {error}\n")


if __name__ == "__main__":
    main()
