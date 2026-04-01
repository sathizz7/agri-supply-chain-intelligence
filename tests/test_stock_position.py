"""Tests for tfais.sections.fertilizer.parsers.stock_position."""
import json
from datetime import datetime, timezone

import pytest

from tfais.sections.fertilizer.parsers.stock_position import (
    DealerRecord,
    StockPositionParser,
    _triage_page,
    _extract_dealer_identity,
    _extract_contact,
    _classify_rows,
    _map_stock_data,
    _compute_structure_signature,
)
from bs4 import BeautifulSoup


class TestTriagePage:

    def test_empty_page_tamil(self):
        soup = BeautifulSoup("<div>தகவல் இல்லை</div>", "lxml")
        assert _triage_page(soup) == "EMPTY"

    def test_empty_page_english(self):
        soup = BeautifulSoup("<div>no data available</div>", "lxml")
        assert _triage_page(soup) == "EMPTY"

    def test_error_page_login(self):
        soup = BeautifulSoup("<div>Please login to continue</div>", "lxml")
        assert _triage_page(soup) == "ERROR"

    def test_has_results(self):
        soup = BeautifulSoup("<div><table><tr><td>data</td></tr></table></div>", "lxml")
        assert _triage_page(soup) == "HAS_RESULTS"

    def test_short_empty_page(self):
        soup = BeautifulSoup("<div></div>", "lxml")
        assert _triage_page(soup) == "EMPTY"


class TestExtractDealerIdentity:

    def test_name_with_code(self):
        html = '<div><h4>தத்தூர் வேளாண்மை சங்கம் (999210)</h4></div>'
        card = BeautifulSoup(html, "lxml").find("div")
        result = _extract_dealer_identity(card)
        assert result["name"] == "தத்தூர் வேளாண்மை சங்கம்"
        assert result["code"] == "999210"

    def test_name_without_code(self):
        html = '<div><strong>Some Dealer Name</strong></div>'
        card = BeautifulSoup(html, "lxml").find("div")
        result = _extract_dealer_identity(card)
        assert result["name"] == "Some Dealer Name"
        assert result["code"] == ""

    def test_empty_card(self):
        html = '<div></div>'
        card = BeautifulSoup(html, "lxml").find("div")
        result = _extract_dealer_identity(card)
        assert result["name"] == ""
        assert result["code"] == ""


class TestExtractContact:

    def test_valid_mobile(self):
        html = '<div>Contact: 9876543210</div>'
        card = BeautifulSoup(html, "lxml").find("div")
        assert _extract_contact(card) == "9876543210"

    def test_no_mobile(self):
        html = '<div>No contact info</div>'
        card = BeautifulSoup(html, "lxml").find("div")
        assert _extract_contact(card) == ""


class TestNgInitParsing:

    def test_parse_ng_init_basic(self):
        fert_data = {
            "0": {
                "tamil_agency": "Test Dealer",
                "dealer_id": "12345",
                "tamil_address": "123 Main St",
                "mobile_number": "9876543210",
                "fert": {
                    "Urea": "0.65",
                    "DAP": "1.2",
                },
            }
        }
        html = f'<div ng-init=\'fert_list={json.dumps(fert_data)}\'></div>'

        parser = StockPositionParser()
        soup = BeautifulSoup(html, "lxml")
        district = {"code": "1", "name_ta": "Test District"}
        block = {"code": "101", "name_ta": "Test Block"}

        records = parser._parse_ng_init(soup, district, block, datetime.now(tz=timezone.utc))

        assert records is not None
        assert len(records) == 1
        assert records[0].dealer_name == "Test Dealer"
        assert records[0].dealer_code == "12345"
        assert records[0].stocks["Urea"] == 650.0   # 0.65 tonnes = 650 kg
        assert records[0].stocks["DAP"] == 1200.0    # 1.2 tonnes = 1200 kg

    def test_parse_ng_init_not_present(self):
        html = '<div>No ng-init here</div>'
        parser = StockPositionParser()
        soup = BeautifulSoup(html, "lxml")
        result = parser._parse_ng_init(soup, {}, {}, datetime.now(tz=timezone.utc))
        assert result is None

    def test_parse_ng_init_with_newlines(self):
        """Test that literal newlines in JSON are handled."""
        fert_data = {"0": {
            "tamil_agency": "Test\nDealer",
            "dealer_id": "99",
            "fert": {"Urea(45\nKg)": "0.5"},
        }}
        json_str = json.dumps(fert_data)
        # Inject literal newlines like the real site does
        json_str = json_str.replace("\\n", "\n")
        html = f"<div ng-init='fert_list={json_str}'></div>"

        parser = StockPositionParser()
        soup = BeautifulSoup(html, "lxml")
        records = parser._parse_ng_init(
            soup, {"code": "1"}, {"code": "101"}, datetime.now(tz=timezone.utc)
        )
        assert records is not None
        assert len(records) == 1


class TestMapStockData:

    def test_basic_mapping(self):
        headers = ["Urea", "DAP"]
        values = ["1650", "200.5"]
        result = _map_stock_data(headers, values)
        assert result["Urea"] == 1650.0
        assert result["DAP"] == 200.5

    def test_unparseable_values(self):
        headers = ["Urea"]
        values = ["N/A"]
        result = _map_stock_data(headers, values)
        assert result["Urea"] == 0.0  # unparseable → 0.0 default


class TestStructureSignature:

    def test_same_headers_same_sig(self):
        sig1 = _compute_structure_signature(["A", "B"], 1)
        sig2 = _compute_structure_signature(["B", "A"], 1)  # order shouldn't matter (sorted)
        assert sig1 == sig2

    def test_different_headers_different_sig(self):
        sig1 = _compute_structure_signature(["A", "B"], 1)
        sig2 = _compute_structure_signature(["A", "C"], 1)
        assert sig1 != sig2
