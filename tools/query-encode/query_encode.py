import argparse
from urllib.parse import urlencode


def encode(pairs):
    fields = []
    for pair in pairs:
        key, separator, value = pair.partition("=")
        if not separator or not key:
            raise ValueError("each argument must have the form name=value with a nonempty name")
        fields.append((key, value))
    return urlencode(fields)


def main():
    parser = argparse.ArgumentParser(description="Encode ordered form query parameters.")
    parser.add_argument("pairs", metavar="name=value", nargs="+")
    args = parser.parse_args()
    try:
        print(encode(args.pairs))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
