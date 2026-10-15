#!/usr/bin/env python3
"""Find paths with identical Unicode-normalized comparison keys."""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import sys
import unicodedata


def comparison_key(path, case_sensitive=False):
    value = unicodedata.normalize("NFC", path)
    if not case_sensitive:
        value = value.casefold()
    return unicodedata.normalize("NFC", value)


def scan_paths(root):
    """Yield relative paths including directories and symlinks, without following links."""
    if root.is_symlink() or not root.is_dir():
        raise OSError("root must be a real directory")
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda entry: entry.name)
        for entry in entries:
            path = Path(entry.path)
            yield path.relative_to(root).as_posix()
            if entry.is_dir(follow_symlinks=False):
                pending.append(path)


def find_collisions(paths, case_sensitive=False, max_groups=20):
    buckets = defaultdict(list)
    count = 0
    for path in paths:
        count += 1
        buckets[comparison_key(path, case_sensitive)].append(path)
    collisions = [sorted(group) for group in buckets.values() if len(group) > 1]
    collisions.sort(key=lambda group: group[0])
    return {
        "ok": not collisions,
        "entry_count": count,
        "case_sensitive": case_sensitive,
        "normalization": "NFC",
        "collision_group_count": len(collisions),
        "colliding_path_count": sum(map(len, collisions)),
        "groups": collisions[:max_groups],
        "omitted_group_count": max(0, len(collisions) - max_groups),
    }


def nonnegative(raw):
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="directory to inspect recursively")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="compare using NFC only, without casefold")
    parser.add_argument("--max-groups", type=nonnegative, default=20,
                        help="maximum displayed groups; all collisions are counted (default: 20)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    try:
        report = find_collisions(scan_paths(args.root), args.case_sensitive, args.max_groups)
    except OSError:
        print("error: root must be a readable directory; scan could not be completed",
              file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    else:
        prefix = "OK" if report["ok"] else "COLLISIONS"
        print(f"{prefix}: {report['collision_group_count']} group(s), "
              f"{report['colliding_path_count']} colliding path(s), "
              f"{report['entry_count']} entry/entries scanned.")
        for number, group in enumerate(report["groups"], 1):
            print(f"Group {number}:")
            for path in group:
                print("  " + json.dumps(path, ensure_ascii=True))
        if report["omitted_group_count"]:
            print(f"{report['omitted_group_count']} further group(s) omitted.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
