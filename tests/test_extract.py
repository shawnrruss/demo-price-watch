import unittest
from decimal import Decimal
from pathlib import Path

from pricewatch.extract import extract_page


class GridExtractionTests(unittest.TestCase):
    def test_grid_fixture_extracts_product_record(self):
        source = Path(__file__).resolve().parents[1] / "fixtures/day1/grid.html"
        self.assertEqual(
            extract_page(source),
            [{
                "sku": "HH-001",
                "name": "Workshop cabinet",
                "price": Decimal("1299.00"),
                "currency": "USD",
                "in_stock": True,
                "url": "https://hearth-harbor.example/products/HH-001",
                "source_file": str(source),
            }],
        )
