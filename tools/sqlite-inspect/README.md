# SQLite Inspect

Inspect SQLite schema metadata through a read-only connection. It reports tables, views, columns, indexes, foreign keys, and triggers in text or JSON without querying table rows.

Requires Python 3.9 or newer and uses its bundled `sqlite3` module.

```bash
python tools/sqlite-inspect/sqlite_inspect.py app.db
python tools/sqlite-inspect/sqlite_inspect.py app.db --json
```

Objects whose names begin with `sqlite_` are omitted unless `--include-internal` is used. The output contains declared column defaults and schema names but not row values or SQL definitions. This is a schema inventory, not an integrity check, migration diff, query analyzer, or guarantee that foreign-key enforcement is enabled. Metadata is loaded into memory.
