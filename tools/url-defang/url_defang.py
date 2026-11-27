"""Defang HTTP(S) URLs for sharing in plain-text reports."""
import argparse
import sys
from pathlib import Path
from urllib.parse import urlsplit


def defang(value):
    parts = urlsplit(value)
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        raise ValueError("expected an absolute HTTP(S) URL")
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise ValueError("URL must not contain whitespace or control characters")
    scheme, remainder = value.split(":", 1)
    return ("hxxps" if scheme.lower() == "https" else "hxxp") + ":" + remainder.replace(".", "[.]")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file containing one URL per line, or -")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        output = []
        for line, raw in enumerate(data.decode("utf-8-sig").splitlines(), 1):
            if not raw:
                continue
            try:
                output.append(defang(raw))
            except ValueError as error:
                raise ValueError(f"line {line}: {error}") from error
        for value in output:
            print(value)
    except (OSError, ValueError) as error:
        parser.exit(1, f"url-defang: {error}\n")


if __name__ == "__main__":
    main()
