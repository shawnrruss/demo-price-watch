import contextlib
import io
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from pricewatch.clean import dedupe, normalize_price
from pricewatch.cli import main
from pricewatch.diff import compare
from pricewatch.extract import extract_directory, extract_page
from pricewatch.report import render
from pricewatch.store import load_run, save_run

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_prices(self):
        for value in ("$1,299.00", "1 299,00 EUR", "1299.00", "1\u00a0299,00 EUR"):
            with self.subTest(value=value):
                self.assertEqual(normalize_price(value), Decimal("1299.00"))
        for value in ("", "free", "NaN", "-1", "12.345", "1,2,3"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_price(value)

    def test_table_and_dedupe(self):
        records = extract_page(ROOT / "fixtures/day1/table.html")
        self.assertEqual([r["sku"] for r in records], ["HH-002", "HH-003"])
        self.assertEqual(records[0]["price"], Decimal("24.00"))
        self.assertEqual(len(dedupe(records + records)), 2)

    def test_changes_and_report(self):
        before, errors = extract_directory(ROOT / "fixtures/day1")
        self.assertEqual(errors, [])
        after, errors = extract_directory(ROOT / "fixtures/day2")
        self.assertEqual(errors, [])
        changes = compare(before, after)
        self.assertEqual([c["type"] for c in changes],
                         ["repriced", "stock", "removed", "new"])
        self.assertEqual(changes[0]["percent"], "-7.70")
        html = render(changes)
        for change in changes:
            self.assertIn(change["sku"], html)
        self.assertIn("<svg", html)
        self.assertIn("-7.70%", html)

    def test_sqlite_roundtrip(self):
        records, _ = extract_directory(ROOT / "fixtures/day1")
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "runs.db"
            save_run(db, "2026-11-01", records)
            self.assertEqual(load_run(db, "2026-11-01"), records)
            save_run(db, "2026-11-01", records[:1])
            self.assertEqual(load_run(db, "2026-11-01"), records[:1])
            with self.assertRaises(ValueError):
                load_run(db, "2026-11-02")

    def test_malformed_and_unknown(self):
        records, errors = extract_directory(ROOT / "fixtures/broken")
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("unknown layout" in e for e in errors))
        self.assertTrue(any("malformed.html: row 1" in e for e in errors))
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()) as err:
            result = main(["--db", str(Path(tmp) / "db"), "extract",
                           str(ROOT / "fixtures/broken"), "--run", "2026-11-01"])
            self.assertEqual(result, 1)
            self.assertIn("unknown layout", err.getvalue())

    def test_cli_outputs_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            common = ["--db", str(Path(tmp) / "db")]
            with contextlib.redirect_stdout(io.StringIO()):
                for day in (1, 2):
                    self.assertEqual(main(common + ["extract", str(ROOT / f"fixtures/day{day}"),
                                                    "--run", f"2026-11-0{day}"]), 0)
            for flag in ("--csv", "--json"):
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(main(common + ["diff", "2026-11-01", "2026-11-02", flag]), 0)
                self.assertIn("HH-004", out.getvalue())
            target = Path(tmp) / "report.html"
            self.assertEqual(main(common + ["report", "2026-11-01", "2026-11-02",
                                            "--html", str(target)]), 0)
            self.assertIn("HH-004", target.read_text(encoding="utf-8"))
