import argparse
import re
import sys
from contextlib import nullcontext


def convert(source, output, ending, chunk_size=65536):
    pending = b""
    for chunk in iter(lambda: source.read(chunk_size), b""):
        data = pending + chunk
        pending = b""
        if data.endswith(b"\r"):
            data, pending = data[:-1], b"\r"
        output.write(re.sub(rb"\r\n|\r|\n", lambda _: ending, data))
    if pending:
        output.write(ending)


def main():
    parser = argparse.ArgumentParser(description="Convert byte-oriented line endings.")
    parser.add_argument("file", nargs="?", default="-", help="Input file or - for stdin")
    parser.add_argument("--to", choices=("lf", "crlf", "cr"), required=True)
    args = parser.parse_args()
    ending = {"lf": b"\n", "crlf": b"\r\n", "cr": b"\r"}[args.to]
    try:
        with (nullcontext(sys.stdin.buffer) if args.file == "-" else open(args.file, "rb")) as source:
            convert(source, sys.stdout.buffer, ending)
            sys.stdout.buffer.flush()
    except OSError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
