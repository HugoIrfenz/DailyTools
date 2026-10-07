#!/usr/bin/env python3
"""Find duplicate files safely using size grouping and SHA-256."""

import argparse
from collections import defaultdict
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


CHUNK_SIZE = 1024 * 1024


def human_bytes(value):
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    number = float(value)
    for unit in units:
        if number < 1024 or unit == units[-1]:
            return f"{int(number)} {unit}" if unit == "B" else f"{number:.1f} {unit}"
        number /= 1024


def excluded(relative, patterns):
    text = relative.as_posix()
    return any(fnmatch.fnmatchcase(text, pattern) or
               fnmatch.fnmatchcase(relative.name, pattern)
               for pattern in patterns)


def hash_file(path, initial_stat):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    final_stat = path.stat(follow_symlinks=False)
    before = (initial_stat.st_dev, initial_stat.st_ino, initial_stat.st_size,
              initial_stat.st_mtime_ns)
    after = (final_stat.st_dev, final_stat.st_ino, final_stat.st_size,
             final_stat.st_mtime_ns)
    if before != after:
        raise OSError("file changed while being hashed")
    return digest.hexdigest()


def scan(root, min_size=1, patterns=()):
    root = Path(root)
    errors = []
    by_size = defaultdict(list)
    seen_physical_files = set()

    try:
        root_stat = root.stat(follow_symlinks=False)
    except OSError as exc:
        return [], [{"path": str(root), "error": str(exc)}], 0
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        return [], [{"path": str(root), "error": "root must be a real directory"}], 0

    def on_walk_error(exc):
        errors.append({"path": exc.filename or str(root), "error": str(exc)})

    for current, directories, files in os.walk(root, followlinks=False,
                                               onerror=on_walk_error):
        current_path = Path(current)
        kept_directories = []
        for name in directories:
            child = current_path / name
            relative = child.relative_to(root)
            if excluded(relative, patterns):
                continue
            try:
                if child.is_symlink():
                    continue
            except OSError as exc:
                errors.append({"path": str(relative), "error": str(exc)})
                continue
            kept_directories.append(name)
        directories[:] = kept_directories

        for name in files:
            path = current_path / name
            relative = path.relative_to(root)
            if excluded(relative, patterns):
                continue
            try:
                info = path.stat(follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode) or info.st_size < min_size:
                    continue
                identity = (info.st_dev, info.st_ino)
                if identity in seen_physical_files:
                    continue
                seen_physical_files.add(identity)
                by_size[info.st_size].append((relative, info))
            except OSError as exc:
                errors.append({"path": relative.as_posix(), "error": str(exc)})

    groups = []
    hashed_count = 0
    for size in sorted(by_size):
        candidates = by_size[size]
        if len(candidates) < 2:
            continue
        by_hash = defaultdict(list)
        for relative, info in candidates:
            try:
                digest = hash_file(root / relative, info)
                hashed_count += 1
                by_hash[digest].append(relative.as_posix())
            except OSError as exc:
                errors.append({"path": relative.as_posix(), "error": str(exc)})
        for digest in sorted(by_hash):
            paths = sorted(by_hash[digest])
            if len(paths) > 1:
                groups.append({"sha256": digest, "size": size, "files": paths,
                               "reclaimable_bytes": size * (len(paths) - 1)})

    groups.sort(key=lambda group: (-group["reclaimable_bytes"], group["files"]))
    errors.sort(key=lambda error: error["path"])
    return groups, errors, hashed_count


def text_report(groups, errors, hashed_count):
    reclaimable = sum(group["reclaimable_bytes"] for group in groups)
    lines = [f"{len(groups)} duplicate group(s); {human_bytes(reclaimable)} potentially reclaimable.",
             f"Hashed {hashed_count} size-matched file(s)."]
    for index, group in enumerate(groups, 1):
        lines.append("")
        lines.append(f"Group {index}: {len(group['files'])} files × "
                     f"{human_bytes(group['size'])}; reclaimable "
                     f"{human_bytes(group['reclaimable_bytes'])}")
        lines.extend(f"  {path}" for path in group["files"])
    if errors:
        lines.append("")
        lines.append(f"{len(errors)} error(s):")
        lines.extend(f"  {error['path']}: {error['error']}" for error in errors)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="directory to scan recursively")
    parser.add_argument("--min-size", type=int, default=1, metavar="BYTES",
                        help="ignore files smaller than BYTES (default: 1; empty files ignored)")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                        help="exclude matching relative paths or names (repeatable)")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args(argv)

    if args.min_size < 0:
        print("error: --min-size cannot be negative", file=sys.stderr)
        return 2

    groups, errors, hashed_count = scan(args.directory, args.min_size, args.exclude)
    reclaimable = sum(group["reclaimable_bytes"] for group in groups)
    if args.json:
        print(json.dumps({"duplicate_group_count": len(groups),
                          "reclaimable_bytes": reclaimable,
                          "hashed_file_count": hashed_count,
                          "groups": groups, "errors": errors},
                         ensure_ascii=False, separators=(",", ":")))
    else:
        print(text_report(groups, errors, hashed_count))
    if errors:
        return 2
    return 1 if groups else 0


if __name__ == "__main__":
    sys.exit(main())
