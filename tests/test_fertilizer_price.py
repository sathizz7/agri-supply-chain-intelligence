"""Tests for tfais.sections.fertilizer.parsers.fertilizer_price."""
from datetime import datetime, timezone

import pytest

from tfais.sections.fertilizer.parsers.fertilizer_price import (
    FertilizerPriceParser,
    PriceRecord,
)


class TestProductDiscovery:

    def test_discover_products_from_html(self):
        from bs4 import BeautifulSoup
        html = """
        <select id="fert_id">
            <option value="0">--Select--</option>
            <option value="1">UREA</option>
            <option value="2">DAP</option>
            <option value="3">MOP</option>
        </select>
        """
        parser = FertilizerPriceParser()
        soup = BeautifulSoup(html, "lxml")
        products = parser._discover_products(soup)
        assert products == {1: "UREA", 2: "DAP", 3: "MOP"}

    def test_discover_products_no_select(self):
        from bs4 import BeautifulSoup
        html = "<div>No select here</div>"
        parser = FertilizerPriceParser()
        soup = BeautifulSoup(html, "lxml")
        products = parser._discover_products(soup)
        assert products == {}

    def test_discover_products_skips_zero(self):
        from bs4 import BeautifulSoup
        html = """
        <select id="fert_id">
            <option value="0">--Select--</option>
            <option value="1">UREA</option>
        </select>
        """
        parser = FertilizerPriceParser()
        soup = BeautifulSoup(html, "lxml")
        products = parser._discover_products(soup)
        assert 0 not in products
        assert 1 in products


class TestParsing:

    def test_parse_basic(self):
        parser = FertilizerPriceParser()
        raw = [
            {
                "product_id": 1,
                "product_name": "UREA",
                "entries": [
                    {"company": "IFFCO", "price": "266.50"},
                    {"company": "KRIBHCO", "price": "266.50"},
                ],
            }
        ]
        records = parser.parse(raw)
        assert len(records) == 2
        assert records[0].product_name == "UREA"
        assert records[0].company == "IFFCO"
        assert records[0].price_per_50kg == 266.50

    def test_parse_empty_entries(self):
        parser = FertilizerPriceParser()
        raw = [{"product_id": 99, "product_name": "EMPTY", "entries": []}]
        records = parser.parse(raw)
        assert len(records) == 0

    def test_parse_skips_empty_company(self):
        parser = FertilizerPriceParser()
        raw = [
            {
                "product_id": 1,
                "product_name": "UREA",
                "entries": [
                    {"company": "", "price": "100"},
                    {"company": "IFFCO", "price": "266.50"},
                ],
            }
        ]
        records = parser.parse(raw)
        assert len(records) == 1
        assert records[0].company == "IFFCO"

    def test_parse_unparseable_price(self):
        parser = FertilizerPriceParser()
        raw = [
            {
                "product_id": 1,
                "product_name": "UREA",
                "entries": [{"company": "TEST", "price": "N/A"}],
            }
        ]
        records = parser.parse(raw)
        assert len(records) == 1
        assert records[0].price_per_50kg is None

    def test_parse_price_with_commas(self):
        parser = FertilizerPriceParser()
        raw = [
            {
                "product_id": 1,
                "product_name": "UREA",
                "entries": [{"company": "TEST", "price": "1,266.50"}],
            }
        ]
        records = parser.parse(raw)
        assert records[0].price_per_50kg == 1266.50


class TestValidation:

    def _make_records(self, prices: list[float]) -> list[PriceRecord]:
        now = datetime.now(tz=timezone.utc)
        return [
            PriceRecord(
                product_id=i,
                product_name=f"Product_{i}",
                company=f"Company_{i}",
                price_per_50kg=p,
                scraped_at=now,
            )
            for i, p in enumerate(prices)
        ]

    def test_validate_negative_price(self):
        parser = FertilizerPriceParser()
        records = self._make_records([100.0, -50.0, 200.0])

        # Mock session that returns 0 for previous count
        class MockSession:
            def scalar(self, *a, **kw):
                return None
            def scalars(self, *a, **kw):
                class R:
                    def all(self):
                        return []
                return R()

        anomalies = parser.validate(records, MockSession())
        negative_anomalies = [a for a in anomalies if a["anomaly_type"] == "negative_price"]
        assert len(negative_anomalies) == 1
        assert "Product_1" in negative_anomalies[0]["detail"]

    def test_validate_price_spike(self):
        parser = FertilizerPriceParser()
        # Median of [100, 200, 300] is 200. 5000 > 200*10
        records = self._make_records([100.0, 200.0, 300.0, 5000.0])

        class MockSession:
            def scalar(self, *a, **kw):
                return None
            def scalars(self, *a, **kw):
                class R:
                    def all(self):
                        return []
                return R()

        anomalies = parser.validate(records, MockSession())
        spike_anomalies = [a for a in anomalies if a["anomaly_type"] == "price_spike"]
        assert len(spike_anomalies) == 1
