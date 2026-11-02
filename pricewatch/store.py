"""SQLite snapshots, with one date-keyed table per run."""
import re
import sqlite3
from contextlib import closing
from datetime import date
from decimal import Decimal
from pathlib import Path

FIELDS = "sku, name, price, currency, in_stock, url, source_file"


def table_name(run):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", run):
        raise ValueError("run must be YYYY-MM-DD")
    date.fromisoformat(run)
    return "run_" + run.replace("-", "_")


def save_run(database, run, records):
    table = table_name(run)
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as db, db:
        db.execute(f"CREATE TABLE IF NOT EXISTS {table} (sku TEXT PRIMARY KEY, name TEXT, "
                   "price TEXT, currency TEXT, in_stock INTEGER, url TEXT, source_file TEXT)")
        db.execute(f"DELETE FROM {table}")
        db.executemany(f"INSERT INTO {table} ({FIELDS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       [(r["sku"], r["name"], str(r["price"]), r["currency"],
                         int(r["in_stock"]), r["url"], r["source_file"]) for r in records])


def load_run(database, run):
    table = table_name(run)
    with closing(sqlite3.connect(database)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                          (table,)).fetchone():
            raise ValueError(f"unknown run: {run}")
        db.row_factory = sqlite3.Row
        records = [dict(row) for row in db.execute(f"SELECT {FIELDS} FROM {table} ORDER BY rowid")]
    for record in records:
        record["price"] = Decimal(record["price"])
        record["in_stock"] = bool(record["in_stock"])
    return records
