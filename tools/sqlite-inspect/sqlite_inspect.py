#!/usr/bin/env python3
"""Inspect SQLite schema metadata through a read-only connection."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional


def connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def columns_for(connection: sqlite3.Connection, name: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        'SELECT cid, name, type, "notnull", dflt_value, pk, hidden '
        'FROM pragma_table_xinfo(?) ORDER BY cid',
        (name,),
    )
    return [
        {
            "position": row["cid"],
            "name": row["name"],
            "type": row["type"],
            "not_null": bool(row["notnull"]),
            "default": row["dflt_value"],
            "primary_key_position": row["pk"],
            "hidden": row["hidden"],
        }
        for row in rows
    ]


def indexes_for(connection: sqlite3.Connection, name: str) -> list[dict[str, Any]]:
    indexes: list[dict[str, Any]] = []
    rows = connection.execute(
        'SELECT seq, name, "unique", origin, partial '
        'FROM pragma_index_list(?) ORDER BY seq',
        (name,),
    )
    for row in rows:
        column_rows = connection.execute(
            "SELECT seqno, cid, name FROM pragma_index_info(?) ORDER BY seqno",
            (row["name"],),
        )
        indexes.append(
            {
                "name": row["name"],
                "unique": bool(row["unique"]),
                "origin": row["origin"],
                "partial": bool(row["partial"]),
                "columns": [column["name"] for column in column_rows],
            }
        )
    return indexes


def foreign_keys_for(connection: sqlite3.Connection, name: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        'SELECT id, seq, "table", "from", "to", on_update, on_delete, match '
        'FROM pragma_foreign_key_list(?) ORDER BY id, seq',
        (name,),
    )
    return [
        {
            "id": row["id"],
            "sequence": row["seq"],
            "from": row["from"],
            "table": row["table"],
            "to": row["to"],
            "on_update": row["on_update"],
            "on_delete": row["on_delete"],
            "match": row["match"],
        }
        for row in rows
    ]


def inspect_database(path: Path, include_internal: bool = False) -> dict[str, Any]:
    with connect_readonly(path) as connection:
        filter_sql = "" if include_internal else " AND substr(name, 1, 7) <> 'sqlite_'"
        objects = connection.execute(
            "SELECT type, name FROM sqlite_schema "
            "WHERE type IN ('table', 'view')" + filter_sql + " ORDER BY type, name"
        ).fetchall()
        triggers = connection.execute(
            "SELECT name, tbl_name FROM sqlite_schema WHERE type = 'trigger'"
            + filter_sql
            + " ORDER BY name"
        ).fetchall()

        tables: list[dict[str, Any]] = []
        views: list[dict[str, Any]] = []
        for row in objects:
            item = {
                "name": row["name"],
                "columns": columns_for(connection, row["name"]),
                "indexes": indexes_for(connection, row["name"]),
                "foreign_keys": foreign_keys_for(connection, row["name"]),
            }
            (tables if row["type"] == "table" else views).append(item)

        return {
            "database": str(path),
            "sqlite_version": sqlite3.sqlite_version,
            "tables": tables,
            "views": views,
            "triggers": [
                {"name": row["name"], "table": row["tbl_name"]} for row in triggers
            ],
        }


def render_text(summary: dict[str, Any]) -> str:
    lines = [
        f"database: {summary['database']}",
        f"SQLite: {summary['sqlite_version']}",
        f"tables: {len(summary['tables'])}",
        f"views: {len(summary['views'])}",
        f"triggers: {len(summary['triggers'])}",
    ]
    for kind in ("tables", "views"):
        singular = kind[:-1]
        for item in summary[kind]:
            lines.append(f"{singular} {item['name']}")
            for column in item["columns"]:
                attributes = []
                if column["not_null"]:
                    attributes.append("NOT NULL")
                if column["primary_key_position"]:
                    attributes.append(f"PK#{column['primary_key_position']}")
                if column["hidden"]:
                    attributes.append(f"hidden={column['hidden']}")
                suffix = f" [{' '.join(attributes)}]" if attributes else ""
                lines.append(f"  column {column['name']} {column['type']}{suffix}")
            for index in item["indexes"]:
                flags = [index["origin"]]
                if index["unique"]:
                    flags.append("unique")
                if index["partial"]:
                    flags.append("partial")
                lines.append(
                    f"  index {index['name']} ({', '.join(index['columns'])}) "
                    f"[{' '.join(flags)}]"
                )
            for foreign_key in item["foreign_keys"]:
                lines.append(
                    f"  foreign key {foreign_key['from']} -> "
                    f"{foreign_key['table']}.{foreign_key['to']}"
                )
    for trigger in summary["triggers"]:
        lines.append(f"trigger {trigger['name']} on {trigger['table']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect SQLite schema metadata.")
    parser.add_argument("database", type=Path)
    parser.add_argument("--include-internal", action="store_true", help="include sqlite_ objects")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = inspect_database(args.database, args.include_internal)
    except (OSError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
