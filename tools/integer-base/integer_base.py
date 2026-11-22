"""Convert a signed integer between bases 2 through 36."""
import argparse

DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def convert(value, source, destination):
    sign = ""
    if value.startswith(("+", "-")):
        sign, value = value[0], value[1:]
    if not value or any(character.lower() not in DIGITS[:source] for character in value):
        raise ValueError("input must contain digits valid for the source base")
    number = int(sign + value, source)
    negative = number < 0
    number = abs(number)
    result = []
    while number:
        number, remainder = divmod(number, destination)
        result.append(DIGITS[remainder])
    return ("-" if negative else "") + ("".join(reversed(result)) or "0")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("value")
    parser.add_argument("--from", dest="source", type=int, choices=range(2, 37), required=True)
    parser.add_argument("--to", type=int, choices=range(2, 37), required=True)
    args = parser.parse_args()
    try:
        print(convert(args.value, args.source, args.to))
    except ValueError as error:
        parser.exit(1, f"integer-base: {error}\n")


if __name__ == "__main__":
    main()
