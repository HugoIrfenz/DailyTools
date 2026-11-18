"""Calculate the contrast ratio between two opaque sRGB colors."""
import argparse
import re


def color(value):
    digits = value.removeprefix("#")
    if not re.fullmatch(r"(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", digits):
        raise argparse.ArgumentTypeError("expected three or six hexadecimal digits")
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    return bytes.fromhex(digits)


def linearize(channel):
    value = channel / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    return sum(weight * linearize(channel)
               for channel, weight in zip(rgb, (0.2126, 0.7152, 0.0722)))


def contrast(first, second):
    dark, light = sorted((luminance(first), luminance(second)))
    return (light + 0.05) / (dark + 0.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=color)
    parser.add_argument("second", type=color)
    args = parser.parse_args()
    print(f"{contrast(args.first, args.second):.4f}:1")


if __name__ == "__main__":
    main()
