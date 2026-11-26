# CSV Rename

Rename columns in UTF-8 comma-delimited CSV. Requires Python 3.9+ with no third-party packages.

```bash
printf 'id,name\n1,Ana\n' | python tools/csv-rename/csv_rename.py - --rename name full_name
python tools/csv-rename/csv_rename.py people.csv --rename id user_id --rename name full_name > renamed.csv
```

The example header becomes `id,full_name`. Renames happen simultaneously, so two columns can swap names. Header names must be unique and resulting names nonempty. Rows retain their values and column order. Output uses CSV quoting and CRLF. A later malformed row can leave earlier output on stdout.
