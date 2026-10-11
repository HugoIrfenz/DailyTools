#!/usr/bin/env python3
"""Create and verify deterministic SHA-256 manifests for directory trees."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile


FORMAT = "dailytools-hash-manifest-v1"
CHUNK_SIZE = 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ToolError(Exception):
    pass


def validate_root(root):
    try:
        info = root.lstat()
    except OSError as exc:
        raise ToolError("root directory is not readable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ToolError("root must be a real directory, not a file or symlink")


def validate_relative_path(raw):
    if not isinstance(raw, str) or not raw:
        raise ToolError("manifest contains an empty or non-string path")
    if "\\" in raw or ":" in raw or any(ord(char) < 32 or ord(char) == 127 for char in raw):
        raise ToolError("manifest path contains an unsupported character")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ToolError("manifest path is not a safe relative path")
    if path.as_posix() != raw:
        raise ToolError("manifest path is not in canonical POSIX form")
    return path


def hash_regular_file(path):
    flags = os.O_RDONLY
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ToolError("file could not be opened for hashing") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ToolError("path changed or is not a regular file")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while True:
                chunk = handle.read(CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
        after = os.fstat(descriptor)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if identity_before != identity_after:
            raise ToolError("file changed while it was being hashed")
        return digest.hexdigest(), after.st_size
    except OSError as exc:
        raise ToolError("file could not be read for hashing") from exc
    finally:
        os.close(descriptor)


def scan_tree(root, excluded=None, include_hashes=True):
    excluded = excluded or set()
    records = []
    skipped_symlinks = 0
    skipped_special = 0

    def walk_error(error):
        raise error

    try:
        for directory, dirnames, filenames in os.walk(root, topdown=True,
                                                       followlinks=False, onerror=walk_error):
            directory_path = Path(directory)
            kept_dirs = []
            for name in sorted(dirnames):
                candidate = directory_path / name
                if candidate.is_symlink():
                    skipped_symlinks += 1
                else:
                    kept_dirs.append(name)
            dirnames[:] = kept_dirs
            for name in sorted(filenames):
                candidate = directory_path / name
                absolute = Path(os.path.abspath(candidate))
                if absolute in excluded:
                    continue
                relative = candidate.relative_to(root).as_posix()
                validate_relative_path(relative)
                info = candidate.lstat()
                if stat.S_ISLNK(info.st_mode):
                    skipped_symlinks += 1
                    continue
                if not stat.S_ISREG(info.st_mode):
                    skipped_special += 1
                    continue
                record = {"path": relative}
                if include_hashes:
                    digest, size = hash_regular_file(candidate)
                    record.update({"size": size, "sha256": digest})
                records.append(record)
    except (OSError, ToolError) as exc:
        if isinstance(exc, ToolError):
            raise
        raise ToolError("directory tree could not be scanned") from exc
    records.sort(key=lambda item: item["path"])
    return records, skipped_symlinks, skipped_special


def atomic_write_json(path, data, force=False):
    if path.exists() and not force:
        raise ToolError("manifest already exists; use --force to replace it")
    if not path.parent.is_dir():
        raise ToolError("manifest parent directory does not exist")
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix="." + path.name + ".",
                                         suffix=".tmp", delete=False) as handle:
            temp_name = handle.name
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except OSError as exc:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        raise ToolError("manifest could not be written") from exc


def create_manifest(root, manifest, force=False):
    validate_root(root)
    manifest_absolute = Path(os.path.abspath(manifest))
    records, symlinks, special = scan_tree(root, {manifest_absolute})
    document = {"algorithm": "sha256", "files": records, "format": FORMAT}
    atomic_write_json(manifest, document, force)
    return {
        "ok": True, "mode": "create", "file_count": len(records),
        "total_bytes": sum(item["size"] for item in records),
        "skipped_symlink_count": symlinks, "skipped_special_count": special,
    }


def load_manifest(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ToolError("manifest is not readable UTF-8 JSON") from exc
    if not isinstance(document, dict) or document.get("format") != FORMAT:
        raise ToolError("manifest format is missing or unsupported")
    if document.get("algorithm") != "sha256" or not isinstance(document.get("files"), list):
        raise ToolError("manifest algorithm or file list is invalid")
    records = []
    seen = set()
    for item in document["files"]:
        if not isinstance(item, dict):
            raise ToolError("manifest file entry is not an object")
        relative = validate_relative_path(item.get("path"))
        raw_path = relative.as_posix()
        size = item.get("size")
        digest = item.get("sha256")
        if raw_path in seen:
            raise ToolError("manifest contains a duplicate path")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ToolError("manifest contains an invalid file size")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ToolError("manifest contains an invalid SHA-256 digest")
        seen.add(raw_path)
        records.append({"path": raw_path, "size": size, "sha256": digest})
    return records


def inspect_target(root, relative):
    parts = PurePosixPath(relative).parts
    current = root
    for part in parts[:-1]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            return None, "missing"
        except OSError:
            return None, "read_error"
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return None, "type_mismatch"
    target = current / parts[-1]
    try:
        info = target.lstat()
    except FileNotFoundError:
        return target, "missing"
    except OSError:
        return target, "read_error"
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return target, "type_mismatch"
    return target, None


def verify_manifest(root, manifest, check_extra=False, max_issues=20):
    validate_root(root)
    records = load_manifest(manifest)
    report = {
        "ok": True, "mode": "verify", "expected_file_count": len(records),
        "matched_file_count": 0, "error_count": 0, "issues": [],
        "skipped_symlink_count": 0, "skipped_special_count": 0,
    }

    def issue(code, path, message, **details):
        report["error_count"] += 1
        if len(report["issues"]) < max_issues:
            report["issues"].append({"code": code, "path": path,
                                     "message": message, **details})

    expected_paths = {item["path"] for item in records}
    for item in records:
        target, problem = inspect_target(root, item["path"])
        if problem:
            messages = {
                "missing": "expected file is missing",
                "read_error": "expected path could not be inspected",
                "type_mismatch": "expected path is not a regular file or crosses a symlink",
            }
            issue(problem, item["path"], messages[problem])
            continue
        try:
            digest, size = hash_regular_file(target)
        except ToolError:
            issue("read_error", item["path"], "expected file could not be hashed")
            continue
        if digest != item["sha256"] or size != item["size"]:
            issue("modified", item["path"], "file content or size does not match",
                  expected_size=item["size"], actual_size=size)
        else:
            report["matched_file_count"] += 1

    if check_extra:
        excluded = {Path(os.path.abspath(manifest))}
        current, symlinks, special = scan_tree(root, excluded, include_hashes=False)
        report["skipped_symlink_count"] = symlinks
        report["skipped_special_count"] = special
        for item in current:
            if item["path"] not in expected_paths:
                issue("extra", item["path"], "regular file is not listed in the manifest")

    report["ok"] = report["error_count"] == 0
    report["omitted_issue_count"] = report["error_count"] - len(report["issues"])
    return report


def nonnegative(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return number


def text_report(report):
    if report["mode"] == "create":
        return (f"CREATED: {report['file_count']} file(s), {report['total_bytes']} byte(s); "
                f"skipped {report['skipped_symlink_count']} symlink(s) and "
                f"{report['skipped_special_count']} special file(s).")
    prefix = "OK" if report["ok"] else "INVALID"
    lines = [f"{prefix}: {report['matched_file_count']}/{report['expected_file_count']} "
             f"expected file(s) matched; {report['error_count']} issue(s)."]
    for item in report["issues"]:
        suffix = ""
        if item["code"] == "modified":
            suffix = f" (expected {item['expected_size']} bytes, got {item['actual_size']})"
        lines.append(f"{item['path']}: {item['code']} — {item['message']}{suffix}")
    if report["omitted_issue_count"]:
        lines.append(f"{report['omitted_issue_count']} further issue(s) omitted from details.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="create a manifest")
    create.add_argument("root", type=Path)
    create.add_argument("manifest", type=Path)
    create.add_argument("--force", action="store_true", help="replace an existing manifest")
    create.add_argument("--json", action="store_true", help="emit a JSON report")
    verify = subparsers.add_parser("verify", help="verify a manifest")
    verify.add_argument("root", type=Path)
    verify.add_argument("manifest", type=Path)
    verify.add_argument("--check-extra", action="store_true",
                        help="also report regular files absent from the manifest")
    verify.add_argument("--max-issues", type=nonnegative, default=20, metavar="N")
    verify.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            report = create_manifest(args.root, args.manifest, args.force)
        else:
            report = verify_manifest(args.root, args.manifest,
                                     args.check_extra, args.max_issues)
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, separators=(",", ":"))
          if args.json else text_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
