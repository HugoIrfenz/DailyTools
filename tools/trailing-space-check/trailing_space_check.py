"""Report lines ending in ASCII spaces or tabs."""
import argparse
import json
import sys


def check(lines):
    for number, line in enumerate(lines, 1):
        content = line.rstrip("\r\n")
        count = len(content) - len(content.rstrip(" \t"))
        if count:
            yield number, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="UTF-8 files or - for stdin")
    args = parser.parse_args()
    if args.files.count("-") > 1:
        parser.error("stdin may appear only once")
    found = False
    failed = False
    for path in args.files:
        try:
            if path == "-":
                sys.stdin.reconfigure(encoding="utf-8-sig", newline=None)
                findings = list(check(sys.stdin))
            else:
                with open(path, encoding="utf-8-sig") as source:
                    findings = list(check(source))
        except (OSError, UnicodeError) as error:
            print(f"trailing-space-check: {path!r}: {error}", file=sys.stderr)
            failed = True
            continue
        for number, count in findings:
            print(json.dumps({"file": path, "line": number, "count": count}))
        found = found or bool(findings)
    return 2 if failed else int(found)


if __name__ == "__main__":
    sys.exit(main())
