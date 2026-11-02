"""Render the real generated HTML report to a readable portfolio PNG (Pillow dev-only)."""
import argparse
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", default="out/report.html")
    parser.add_argument("--output", default="docs/preview.png")
    args = parser.parse_args()
    soup = BeautifulSoup(Path(args.html).read_text(encoding="utf-8"), "html.parser")
    rows = [[cell.get_text() for cell in row.select("th, td")]
            for row in soup.select("table tr")]
    bars = soup.select("svg rect")
    labels = [node.get_text() for node in soup.select("svg text")]
    image = Image.new("RGB", (1500, max(850, 450 + len(rows) * 55 + len(bars) * 55)), "#eef3f7")
    draw = ImageDraw.Draw(image)

    def font(size):
        for candidate in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, size)
        return ImageFont.load_default(size=size)

    draw.rounded_rectangle((40, 40, 1460, image.height - 40), radius=22, fill="white")
    draw.text((75, 70), soup.h1.get_text(), font=font(36), fill="#17304a")
    draw.text((75, 130), soup.select_one("main > p").get_text(), font=font(23), fill="#506780")
    draw.text((75, 190), soup.h2.get_text(), font=font(28), fill="#17304a")
    columns = [75, 205, 345, 640, 775, 895, 1070, 1220]
    for index, row in enumerate(rows):
        y = 250 + index * 55
        if index == 0:
            draw.rectangle((65, y - 8, 1430, y + 40), fill="#eef3f7")
        for x, value in zip(columns, row):
            draw.text((x, y), value, font=font(20), fill="#17304a")
        draw.line((65, y + 43, 1430, y + 43), fill="#dce4eb")
    y = 285 + len(rows) * 55
    draw.text((75, y), "Price changes (%)", font=font(28), fill="#17304a")
    for index, bar in enumerate(bars):
        top = y + 60 + index * 55
        draw.text((75, top), labels[index * 2], font=font(22), fill="#17304a")
        draw.rectangle((240, top, 240 + float(bar["width"]) * 1.6, top + 30), fill=bar["fill"])
        draw.text((830, top), labels[index * 2 + 1], font=font(22), fill="#17304a")
    draw.text((75, image.height - 100), soup.select("main > p")[-1].get_text(),
              font=font(21), fill="#506780")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


if __name__ == "__main__":
    main()
