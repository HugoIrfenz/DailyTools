import argparse
import re
import sys
from pathlib import Path

STAMP = r"[0-9]{2,}:[0-5][0-9]:[0-5][0-9],[0-9]{3}"
TIMING = re.compile(fr"({STAMP}) --> ({STAMP})([ \t].*)?")


def milliseconds(stamp):
    hours, minutes, seconds, fraction = map(int, re.split("[:,]", stamp))
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + fraction


def timestamp(value):
    seconds, fraction = divmod(value, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{fraction:03}"


def shift(text, offset):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    cues = re.split(r"\n(?:[ \t]*\n)+", text.strip("\n"))
    for index, cue in enumerate(cues):
        lines = cue.split("\n")
        match = TIMING.fullmatch(lines[1]) if len(lines) >= 3 else None
        if not match or not re.fullmatch(r"[0-9]+", lines[0]):
            raise ValueError(f"invalid cue {index + 1}")
        start, end = (milliseconds(stamp) + offset for stamp in match.group(1, 2))
        if start < 0 or end < start:
            raise ValueError(f"invalid shifted interval in cue {index + 1}")
        lines[1] = f"{timestamp(start)} --> {timestamp(end)}{match[3] or ''}"
        cues[index] = "\n".join(lines)
    return "\n\n".join(cues) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Shift SRT timestamps by milliseconds.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--ms", type=int, required=True)
    args = parser.parse_args()
    try:
        print(shift(args.file.read_text(encoding="utf-8-sig"), args.ms), end="")
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
