"""Extract configured product records from saved HTML."""
import json
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .clean import dedupe, normalize_price


def extract_page(source, errors=None, config=None):
    source = Path(source)
    layouts = json.loads(Path(config or Path(__file__).with_name("selectors.json"))
                         .read_text(encoding="utf-8"))
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
    for selectors in layouts.values():
        page = soup.select_one(selectors["page"])
        if page is not None:
            break
    else:
        raise ValueError(f"{source}: unknown layout")
    rows = page.select(selectors["rows"])
    if not rows:
        raise ValueError(f"{source}: layout contains no product rows")
    records = []
    for number, row in enumerate(rows, 1):
        try:
            def field(key, row=row):
                spec = selectors[key]
                node = row if spec["selector"] == ":self" else row.select_one(spec["selector"])
                if node is None:
                    raise ValueError(f"missing {key}")
                value = node.get(spec["attribute"], "") if "attribute" in spec else node.get_text(strip=True)
                if not value.strip():
                    raise ValueError(f"missing {key}")
                return value.strip()

            record = {key: field(key) for key in
                      ("sku", "name", "price", "currency", "in_stock", "url")}
            record["price"] = normalize_price(record["price"])
            if record["currency"] not in ("USD", "EUR", "GBP"):
                raise ValueError("unsupported currency")
            if record["in_stock"] not in ("in", "out"):
                raise ValueError("invalid stock value")
            if urlparse(record["url"]).scheme not in ("http", "https"):
                raise ValueError("invalid product URL")
            record["in_stock"] = record["in_stock"] == "in"
            record["source_file"] = str(source)
            records.append(record)
        except ValueError as exc:
            message = f"{source}: row {number}: {exc}"
            if errors is None:
                raise ValueError(message) from exc
            errors.append(message)
    return records


def extract_directory(directory, config=None):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"{directory}: not a directory")
    pages = sorted(directory.rglob("*.html"))
    if not pages:
        raise ValueError(f"{directory}: no HTML pages")
    records, errors = [], []
    for page in pages:
        try:
            records.extend(extract_page(page, errors, config))
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    return dedupe(records), errors
