"""Self-contained HTML with escaped table cells and an inline SVG chart."""
from decimal import Decimal
from html import escape


def render(changes, run_a="2026-11-01", run_b="2026-11-02"):
    rows = []
    bars = []
    prices = [c for c in changes if c["type"] == "repriced" and c["percent"]]
    scale = max([abs(Decimal(c["percent"])) for c in prices] + [Decimal(1)])
    for c in changes:
        values = [c["type"], c["sku"], c["name"], c["old"], c["new"],
                  c.get("old_currency", c["currency"]), c["currency"],
                  c["percent"] + "%" if c["percent"] else "n/a"]
        rows.append("<tr>" + "".join(f"<td>{escape(v)}</td>" for v in values) + "</tr>")
    for i, c in enumerate(prices):
        y = 30 + i * 45
        width = float(abs(Decimal(c["percent"])) / scale * 340)
        color = "#17756a" if Decimal(c["percent"]) < 0 else "#b44b30"
        bars.append(f'<text x="12" y="{y + 17}">{escape(c["sku"])}</text>'
                    f'<rect x="110" y="{y}" width="{width}" height="25" fill="{color}"/>'
                    f'<text x="470" y="{y + 17}">{escape(c["percent"])}%</text>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Pricewatch change report</title><style>'
            'body{font:16px system-ui;background:#eef3f7;color:#17304a;margin:40px}'
            'main{max-width:1100px;margin:auto;background:white;padding:32px;border-radius:16px}'
            'table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px;'
            'border-bottom:1px solid #dce4eb}svg{max-width:100%;height:auto}'
            '</style></head><body><main><h1>Hearth Harbor Tools Demo</h1>'
            f'<p>Pricewatch &middot; {escape(run_a)} &rarr; {escape(run_b)}</p>'
            f'<h2>{len(changes)} changes</h2><table><thead><tr>'
            '<th>Type</th><th>SKU</th><th>Name</th><th>Old</th><th>New</th>'
            '<th>Old currency</th><th>Currency</th><th>Percent</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table><h2>Price changes (%)</h2>'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 {max(110, len(prices)*45+45)}" '
            'role="img" aria-label="Price changes as percentages; negative values are decreases">'
            + ''.join(bars) + '</svg><p>Original demo &middot; fictional data &middot; offline saved pages</p>'
            '</main></body></html>')
