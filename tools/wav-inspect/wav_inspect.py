"""Print audio metadata from a local PCM WAV header."""

import argparse
import json
import wave


def inspect(path):
    with wave.open(path, "rb") as source:
        channels, width, rate, frames, _, _ = source.getparams()
    if rate <= 0:
        raise ValueError("sample rate must be positive")
    return {
        "channels": channels,
        "bits_per_sample": width * 8,
        "sample_rate_hz": rate,
        "frames": frames,
        "duration_seconds": frames / rate,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="path to a PCM WAV file")
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.file), indent=2))
    except (OSError, EOFError, ValueError, wave.Error) as error:
        parser.exit(1, f"wav-inspect: {error or 'incomplete WAV header'}\n")


if __name__ == "__main__":
    main()
