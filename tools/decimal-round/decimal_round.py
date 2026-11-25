"""Round finite decimal numbers to a fixed number of fractional places."""
import argparse
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN, ROUND_HALF_UP


def rounded(raw, places, mode):
    value = Decimal(raw)
    if not value.is_finite() or abs(value.adjusted()) > 1000 or len(value.as_tuple().digits) > 1000:
        raise ValueError("expected a finite decimal within 1000 digits/exponent")
    with localcontext() as context:
        context.prec = max(28, value.adjusted() + places + 3)
        result = value.quantize(Decimal(1).scaleb(-places), rounding=mode)
    return format(result, f".{places}f")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("values", nargs="+")
    parser.add_argument("--places", type=int, default=2)
    parser.add_argument("--mode", choices=("half-even", "half-up"), default="half-even")
    args = parser.parse_args()
    if not 0 <= args.places <= 1000:
        parser.error("places must be between 0 and 1000")
    try:
        mode = ROUND_HALF_EVEN if args.mode == "half-even" else ROUND_HALF_UP
        output = [rounded(value, args.places, mode) for value in args.values]
    except (InvalidOperation, ValueError) as error:
        parser.exit(1, f"decimal-round: {error}\n")
    print("\n".join(output))


if __name__ == "__main__":
    main()
