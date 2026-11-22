"""Quote arguments as a POSIX shell command line."""
import argparse
import shlex


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arguments", nargs="*")
    args = parser.parse_args()
    if any("\0" in value for value in args.arguments):
        parser.error("arguments cannot contain NUL")
    print(shlex.join(args.arguments))


if __name__ == "__main__":
    main()
