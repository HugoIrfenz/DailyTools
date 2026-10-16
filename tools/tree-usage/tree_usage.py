#!/usr/bin/env python3
"""Summarize regular-file counts and logical bytes by final extension."""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import stat
import sys


def summarize(root, top=10):
    if root.is_symlink() or not root.is_dir():
        raise OSError("root must be a real directory")
    groups = defaultdict(lambda: {"file_count": 0, "bytes": 0})
    pending = [root]
    files = size = symlinks = special = 0
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as iterator:
            for entry in iterator:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    symlinks += 1
                elif stat.S_ISDIR(info.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    extension = Path(entry.name).suffix.casefold()
                    group = groups[extension]
                    group["file_count"] += 1
                    group["bytes"] += info.st_size
                    files += 1
                    size += info.st_size
                else:
                    special += 1
    ordered = [{"extension": extension, **values} for extension, values in groups.items()]
    ordered.sort(key=lambda item: (-item["bytes"], item["extension"]))
    return {"file_count": files, "total_bytes": size,
            "skipped_symlink_count": symlinks, "skipped_special_count": special,
            "extension_count": len(ordered), "groups": ordered[:top],
            "omitted_group_count": max(0, len(ordered) - top)}


def nonnegative(raw):
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--top", type=nonnegative, default=10, help="display up to N extension groups")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = summarize(args.root, args.top)
    except OSError:
        print("error: root must be a readable directory; scan could not be completed",
              file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    else:
        print(f"Files: {report['file_count']}; logical bytes: {report['total_bytes']}")
        for group in report["groups"]:
            label = json.dumps(group["extension"], ensure_ascii=True) if group["extension"] else "(no extension)"
            print(f"{label}: {group['file_count']} file(s), {group['bytes']} byte(s)")
        print(f"Skipped: {report['skipped_symlink_count']} symlink(s), "
              f"{report['skipped_special_count']} special file(s)")
        if report["omitted_group_count"]:
            print(f"{report['omitted_group_count']} further group(s) omitted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
