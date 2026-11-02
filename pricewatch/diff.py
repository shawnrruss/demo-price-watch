"""Compare snapshots by SKU; percentages use the old price as denominator."""
from decimal import Decimal


def compare(before, after):
    old = {r["sku"]: r for r in before}
    new = {r["sku"]: r for r in after}
    changes = []
    for sku in sorted(old.keys() | new.keys()):
        a, b = old.get(sku), new.get(sku)
        base = {"sku": sku, "name": (b or a)["name"]}
        if a is None or b is None:
            changes.append(dict(base, type="new" if a is None else "removed",
                                old="" if a is None else str(a["price"]),
                                new="" if b is None else str(b["price"]),
                                currency=(b or a)["currency"], percent=""))
            continue
        if (a["price"], a["currency"]) != (b["price"], b["currency"]):
            percent = ""
            if a["price"] and a["currency"] == b["currency"]:
                percent = str(((b["price"] - a["price"]) / a["price"] * 100)
                              .quantize(Decimal("0.01")))
            changes.append(dict(base, type="repriced", old=str(a["price"]), new=str(b["price"]),
                                currency=b["currency"], old_currency=a["currency"], percent=percent))
        if a["in_stock"] != b["in_stock"]:
            changes.append(dict(base, type="stock", old=str(a["in_stock"]),
                                new=str(b["in_stock"]), currency=b["currency"], percent=""))
    return changes


def text_output(changes):
    lines = ["type | sku | name | old | new | currency | percent"]
    for c in changes:
        old = c["old"]
        if c.get("old_currency", c["currency"]) != c["currency"]:
            old += " " + c["old_currency"]
        lines.append(" | ".join([c["type"], c["sku"], c["name"], old, c["new"],
                                 c["currency"], c["percent"]]))
    return "\n".join(lines)
