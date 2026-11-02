"""Offline extraction, comparison and reporting commands."""
import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

from .diff import compare, text_output
from .extract import extract_directory
from .report import render
from .store import load_run, save_run


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pricewatch")
    parser.add_argument("--db", default="out/pricewatch.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract")
    extract.add_argument("directory")
    extract.add_argument("--run", required=True)
    extract.add_argument("--config", help="JSON layout selector configuration")
    for name in ("diff", "report"):
        command = commands.add_parser(name)
        command.add_argument("run_a")
        command.add_argument("run_b")
        if name == "diff":
            formats = command.add_mutually_exclusive_group()
            formats.add_argument("--csv", action="store_true")
            formats.add_argument("--json", action="store_true")
        else:
            command.add_argument("--html", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            records, errors = extract_directory(args.directory, args.config)
            for error in errors:
                print(error, file=sys.stderr)
            if errors:
                return 1
            save_run(args.db, args.run, records)
            print(f"Saved {len(records)} records for {args.run}")
        else:
            changes = compare(load_run(args.db, args.run_a), load_run(args.db, args.run_b))
            if args.command == "report":
                target = Path(args.html)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(render(changes, args.run_a, args.run_b), encoding="utf-8", newline="\n")
            elif args.json:
                print(json.dumps(changes, indent=2))
            elif args.csv:
                writer = csv.DictWriter(sys.stdout, fieldnames=["type", "sku", "name", "old", "new",
                                                               "currency", "old_currency", "percent"])
                writer.writeheader()
                writer.writerows(changes)
            else:
                print(text_output(changes))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(str(exc), file=sys.stderr)
        return 1
