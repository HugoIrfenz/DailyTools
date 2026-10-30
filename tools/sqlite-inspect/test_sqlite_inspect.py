import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sqlite_inspect import connect_readonly, inspect_database, render_text


SCRIPT = Path(__file__).with_name("sqlite_inspect.py")


class SqliteInspectTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def create_database(self, path: Path) -> None:
        connection = sqlite3.connect(path)
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE parent (
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL UNIQUE
            );
            CREATE TABLE child (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                note TEXT DEFAULT 'none',
                secret TEXT,
                FOREIGN KEY (parent_id) REFERENCES parent(id)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            );
            CREATE INDEX child_note_idx ON child(note);
            CREATE VIEW child_view AS SELECT id, note FROM child;
            CREATE TRIGGER child_touch AFTER UPDATE ON child BEGIN
                SELECT NEW.id;
            END;
            INSERT INTO parent(id, code) VALUES (1, 'P1');
            INSERT INTO child(parent_id, note, secret) VALUES (1, 'hello', 'do-not-print');
            """
        )
        connection.commit()
        connection.close()

    def test_lists_user_tables_without_internal_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path)
        self.assertEqual([item["name"] for item in summary["tables"]], ["child", "parent"])

    def test_lists_view(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path)
        self.assertEqual([item["name"] for item in summary["views"]], ["child_view"])

    def test_reports_column_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path)
        child = next(item for item in summary["tables"] if item["name"] == "child")
        parent_id = next(column for column in child["columns"] if column["name"] == "parent_id")
        note = next(column for column in child["columns"] if column["name"] == "note")
        self.assertTrue(parent_id["not_null"])
        self.assertEqual(note["default"], "'none'")

    def test_reports_explicit_index_columns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path)
        child = next(item for item in summary["tables"] if item["name"] == "child")
        index = next(item for item in child["indexes"] if item["name"] == "child_note_idx")
        self.assertEqual(index["columns"], ["note"])
        self.assertFalse(index["unique"])

    def test_reports_unique_constraint_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path)
        parent = next(item for item in summary["tables"] if item["name"] == "parent")
        self.assertTrue(any(item["unique"] for item in parent["indexes"]))

    def test_reports_foreign_key_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path)
        child = next(item for item in summary["tables"] if item["name"] == "child")
        foreign_key = child["foreign_keys"][0]
        self.assertEqual(foreign_key["from"], "parent_id")
        self.assertEqual(foreign_key["table"], "parent")
        self.assertEqual(foreign_key["on_update"], "CASCADE")

    def test_reports_trigger_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path)
        self.assertEqual(summary["triggers"], [{"name": "child_touch", "table": "child"}])

    def test_internal_tables_can_be_included(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            summary = inspect_database(path, include_internal=True)
        self.assertIn("sqlite_sequence", [item["name"] for item in summary["tables"]])

    def test_connection_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            connection = connect_readonly(path)
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("CREATE TABLE forbidden(id INTEGER)")
            connection.close()

    def test_row_values_are_not_in_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            encoded = json.dumps(inspect_database(path))
        self.assertNotIn("do-not-print", encoded)

    def test_database_path_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "with space.db")
            self.create_database(path)
            summary = inspect_database(path)
        self.assertEqual(len(summary["tables"]), 2)

    def test_empty_database_has_no_objects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "empty.db")
            sqlite3.connect(path).close()
            summary = inspect_database(path)
        self.assertEqual(summary["tables"], [])
        self.assertEqual(summary["views"], [])

    def test_unusual_table_name_is_handled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "odd.db")
            connection = sqlite3.connect(path)
            connection.execute('CREATE TABLE "odd name" ("strange column" TEXT)')
            connection.close()
            summary = inspect_database(path)
        self.assertEqual(summary["tables"][0]["name"], "odd name")
        self.assertEqual(summary["tables"][0]["columns"][0]["name"], "strange column")

    def test_text_render_includes_counts_and_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            rendered = render_text(inspect_database(path))
        self.assertIn("tables: 2", rendered)
        self.assertIn("table child", rendered)
        self.assertIn("foreign key parent_id -> parent.id", rendered)

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            result = self.run_cli(str(path), "--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(json.loads(result.stdout)["tables"]), 2)

    def test_cli_text_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.db")
            self.create_database(path)
            result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 0)
        self.assertIn("view child_view", result.stdout)

    def test_cli_reports_missing_database(self) -> None:
        result = self.run_cli("missing.db")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_cli_rejects_non_database_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "bad.db")
            path.write_bytes(b"not sqlite")
            result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
