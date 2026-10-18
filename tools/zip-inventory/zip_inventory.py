#!/usr/bin/env python3
"""Summarize ZIP directory metadata without extracting archive members."""

import argparse
from collections import Counter
import json
import sys
import zipfile


def summarize(archive, top=10):
    if not 0 <= top <= 1000:
        raise ValueError("top must be between 0 and 1000")
    entries = archive.infolist()
    files = [(index, entry) for index, entry in enumerate(entries)
             if not entry.is_dir()]
    names = Counter(entry.filename for entry in entries)
    largest = sorted(files, key=lambda item: (-item[1].file_size,
                                             item[1].filename, item[0]))[:top]
    return {
        "entries": len(entries),
        "files": len(files),
        "directories": len(entries) - len(files),
        "uncompressed_bytes": sum(entry.file_size for entry in entries),
        "compressed_bytes": sum(entry.compress_size for entry in entries),
        "encrypted_files": sum(bool(entry.flag_bits & 1) for _, entry in files),
        "duplicate_names": [{"name": name, "count": count}
                            for name, count in sorted(names.items()) if count > 1],
        "largest_files": [{"entry_index": index, "name": entry.filename,
                           "uncompressed_bytes": entry.file_size,
                           "compressed_bytes": entry.compress_size,
                           "encrypted": bool(entry.flag_bits & 1)}
                          for index, entry in largest],
    }


def top_count(value):
    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("top must be an integer") from exc
    if not 0 <= count <= 1000:
        raise argparse.ArgumentTypeError("top must be between 0 and 1000")
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="path to a ZIP file")
    parser.add_argument("--top", type=top_count, default=10,
                        help="number of largest files to show (0..1000; default 10)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        with zipfile.ZipFile(args.archive) as archive:
            result = summarize(archive, args.top)
    except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError) as exc:
        print(f"zip-inventory: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=True))
    else:
        print(f"Entries: {result['entries']} ({result['files']} files, "
              f"{result['directories']} directories)")
        print(f"Bytes: {result['uncompressed_bytes']} uncompressed, "
              f"{result['compressed_bytes']} compressed")
        print(f"Encrypted files: {result['encrypted_files']}")
        for item in result["duplicate_names"]:
            print(f"Duplicate name ({item['count']}): {json.dumps(item['name'])}")
        for item in result["largest_files"]:
            print(f"#{item['entry_index']} {item['uncompressed_bytes']} bytes "
                  f"({item['compressed_bytes']} compressed): {json.dumps(item['name'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
