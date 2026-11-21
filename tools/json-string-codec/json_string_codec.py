"""Encode text as a JSON string or decode one JSON string."""
import argparse
import json
import sys
from pathlib import Path


def transform(text, mode):
    if mode == "encode":
        return json.dumps(text, ensure_ascii=True)
    value = json.loads(text)
    if not isinstance(value, str):
        raise ValueError("expected a JSON string")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("encode", "decode"))
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        output = transform(data.decode("utf-8-sig"), args.mode)
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, ValueError) as error:
        parser.exit(1, f"json-string-codec: {error}\n")


if __name__ == "__main__":
    main()
