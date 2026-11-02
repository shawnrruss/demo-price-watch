"""Price normalization and deterministic first-record deduplication."""
import re
from decimal import Decimal


def normalize_price(value):
    value = re.sub(r"(?:USD|EUR|GBP|[$\u20ac\u00a3]|\s)", "", value)
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d{2}", value):
        value = value.replace(",", "")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d{2}", value):
        value = value.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d+,\d{2}", value):
        value = value.replace(",", ".")
    if not re.fullmatch(r"\d+(?:\.\d{2})?", value):
        raise ValueError("invalid price")
    return Decimal(value).quantize(Decimal("0.01"))


def dedupe(records):
    unique = {}
    for record in records:
        unique.setdefault(record["sku"], record)
    return list(unique.values())
