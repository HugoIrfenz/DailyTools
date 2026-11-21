"""Summarize finite decimal numbers, one per line."""
import argparse
import json
import sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path


def summarize(text):
    numbers = []
    for line, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = Decimal(raw.strip())
        except InvalidOperation as error:
            raise ValueError(f"line {line}: invalid decimal") from error
        if not value.is_finite() or abs(value.adjusted()) > 10000 or len(value.as_tuple().digits) > 10000:
            raise ValueError(f"line {line}: expected a finite decimal within 10000 digits/exponent")
        numbers.append(value)
    if not numbers:
        raise ValueError("no numbers found")
    lowest = min(value.as_tuple().exponent for value in numbers)
    highest = max(value.adjusted() for value in numbers)
    with localcontext() as context:
        context.prec = max(28, highest - lowest + len(str(len(numbers))) + 2)
        total = sum(numbers, Decimal(0))
        mean = total / len(numbers)
    return {"count": len(numbers), "min": str(min(numbers)), "max": str(max(numbers)),
            "sum": str(total), "mean": str(mean)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 file or - for stdin")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else Path(args.input).read_bytes()
        print(json.dumps(summarize(data.decode("utf-8-sig"))))
    except (OSError, ValueError) as error:
        parser.exit(1, f"number-stats: {error}\n")


if __name__ == "__main__":
    main()
