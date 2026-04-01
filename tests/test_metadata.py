"""Tests for tfais.core.metadata."""
from datetime import date

from tfais.core.metadata import extract_last_updated, safe_parse_number


class TestExtractLastUpdated:

    def test_english_format(self):
        html = '<span class="text-danger">Last update date : 29-03-2026</span>'
        assert extract_last_updated(html) == date(2026, 3, 29)

    def test_tamil_format(self):
        html = 'கடைசி புதுப்பிக்கப்பட்ட நாள் : 15-01-2026'
        assert extract_last_updated(html) == date(2026, 1, 15)

    def test_no_date_found(self):
        html = "<div>No date here</div>"
        assert extract_last_updated(html) is None

    def test_invalid_date(self):
        html = "Last update date : 99-99-9999"
        assert extract_last_updated(html) is None

    def test_embedded_in_large_html(self):
        html = """
        <html><body>
        <div class="header">Dashboard</div>
        <span class="text-danger">Last update date : 01-12-2025</span>
        <div class="content">lots of content</div>
        </body></html>
        """
        assert extract_last_updated(html) == date(2025, 12, 1)


class TestSafeParseNumber:

    def test_integer(self):
        assert safe_parse_number("1650") == 1650.0

    def test_float(self):
        assert safe_parse_number("1650.5") == 1650.5

    def test_with_commas(self):
        assert safe_parse_number("1,650") == 1650.0

    def test_with_commas_and_decimal(self):
        assert safe_parse_number("1,266.50") == 1266.5

    def test_zero(self):
        assert safe_parse_number("0") == 0.0

    def test_negative(self):
        assert safe_parse_number("-50") == -50.0

    def test_empty_string(self):
        assert safe_parse_number("") is None

    def test_none_input(self):
        assert safe_parse_number(None) is None

    def test_dash(self):
        assert safe_parse_number("-") is None

    def test_double_dash(self):
        assert safe_parse_number("--") is None

    def test_na(self):
        assert safe_parse_number("N/A") is None

    def test_nil_variants(self):
        assert safe_parse_number("nil") is None
        assert safe_parse_number("Nil") is None
        assert safe_parse_number("NIL") is None

    def test_asterisk(self):
        assert safe_parse_number("*") is None

    def test_whitespace(self):
        assert safe_parse_number("  1650  ") == 1650.0

    def test_garbage(self):
        assert safe_parse_number("abc") is None

    def test_spaces_in_number(self):
        assert safe_parse_number("1 650") == 1650.0
