#!/usr/bin/env python3
"""Count LF, CRLF and bare CR endings without decoding file contents."""

import argparse
import json
from pathlib import Path
import sys


def inspect(chunks):
    lf = crlf = cr = size = 0
    pending_cr = False
    last = None
    for chunk in chunks:
        size += len(chunk)
        for byte in chunk:
            if pending_cr:
                if byte == 10:
                    crlf += 1
                    pending_cr = False
                    last = byte
                    continue
                cr += 1
                pending_cr = False
            if byte == 13:
                pending_cr = True
            elif byte == 10:
                lf += 1
            last = byte
    if pending_cr:
        cr += 1
    kinds = sum(count > 0 for count in (lf, crlf, cr))
    final = last in (10, 13) if size else False
    return {"bytes": size, "lf": lf, "crlf": crlf, "cr": cr,
            "mixed": kinds > 1, "ends_with_newline": final,
            "logical_lines": lf + crlf + cr + (1 if size and not final else 0)}


def read_chunks(handle):
    while True:
        chunk = handle.read(1024 * 1024)
        if not chunk:
            return
        yield chunk


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="file path, or '-' for stdin")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 for mixed endings or nonempty input lacking a final newline")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            report = inspect(read_chunks(sys.stdin.buffer))
        else:
            with Path(args.input).open("rb") as handle:
                report = inspect(read_chunks(handle))
    except OSError:
        print("error: could not read input", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, separators=(",", ":")))
    else:
        print(f"Bytes: {report['bytes']}; lines: {report['logical_lines']}")
        print(f"LF: {report['lf']}; CRLF: {report['crlf']}; CR: {report['cr']}")
        print(f"Mixed: {report['mixed']}; final newline: {report['ends_with_newline']}")
    failed = report["mixed"] or (report["bytes"] > 0 and not report["ends_with_newline"])
    return 1 if args.check and failed else 0


if __name__ == "__main__":
    sys.exit(main())
