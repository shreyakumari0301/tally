"""Tests for analyzer module - CSV parsing and amount handling."""

import pytest
import tempfile
import os

from tally.analyzer import parse_amount, parse_generic_csv
from tally.format_parser import parse_format_string
from tally.merchant_utils import get_all_rules


class TestParseAmount:
    """Tests for parse_amount function with different locales."""

    def test_us_format_simple(self):
        """Parse simple US format amounts."""
        assert parse_amount('123.45') == 123.45
        assert parse_amount('0.99') == 0.99
        assert parse_amount('100') == 100.0

    def test_us_format_with_thousands(self):
        """Parse US format with thousands separator."""
        assert parse_amount('1,234.56') == 1234.56
        assert parse_amount('12,345.67') == 12345.67
        assert parse_amount('1,234,567.89') == 1234567.89

    def test_us_format_with_currency(self):
        """Parse US format with currency symbols."""
        assert parse_amount('$123.45') == 123.45
        assert parse_amount('$1,234.56') == 1234.56
        assert parse_amount('€100.00') == 100.0
        assert parse_amount('£50.00') == 50.0
        assert parse_amount('¥1000') == 1000.0

    def test_us_format_parenthetical_negative(self):
        """Parse parenthetical negatives (accounting format)."""
        assert parse_amount('(123.45)') == -123.45
        assert parse_amount('(1,234.56)') == -1234.56
        assert parse_amount('($50.00)') == -50.0

    def test_us_format_with_whitespace(self):
        """Parse amounts with leading/trailing whitespace."""
        assert parse_amount('  123.45  ') == 123.45
        assert parse_amount('\t$100.00\n') == 100.0

    def test_european_format_simple(self):
        """Parse simple European format amounts."""
        assert parse_amount('123,45', decimal_separator=',') == 123.45
        assert parse_amount('0,99', decimal_separator=',') == 0.99
        assert parse_amount('100', decimal_separator=',') == 100.0

    def test_european_format_with_thousands(self):
        """Parse European format with period as thousands separator."""
        assert parse_amount('1.234,56', decimal_separator=',') == 1234.56
        assert parse_amount('12.345,67', decimal_separator=',') == 12345.67
        assert parse_amount('1.234.567,89', decimal_separator=',') == 1234567.89

    def test_european_format_with_space_thousands(self):
        """Parse European format with space as thousands separator."""
        assert parse_amount('1 234,56', decimal_separator=',') == 1234.56
        assert parse_amount('12 345,67', decimal_separator=',') == 12345.67

    def test_european_format_with_currency(self):
        """Parse European format with currency symbols."""
        assert parse_amount('€1.234,56', decimal_separator=',') == 1234.56
        assert parse_amount('€123,45', decimal_separator=',') == 123.45
        assert parse_amount('$100,00', decimal_separator=',') == 100.0

    def test_european_format_parenthetical_negative(self):
        """Parse European parenthetical negatives."""
        assert parse_amount('(123,45)', decimal_separator=',') == -123.45
        assert parse_amount('(1.234,56)', decimal_separator=',') == -1234.56


class TestParseGenericCsvDecimalSeparator:
    """Tests for parse_generic_csv with decimal_separator option."""

    def test_us_format_csv(self):
        """Parse CSV with US number format (default)."""
        csv_content = """Date,Description,Amount
01/15/2025,GROCERY STORE,123.45
01/16/2025,COFFEE SHOP,5.99
01/17/2025,BIG PURCHASE,"1,234.56"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()

            rules = get_all_rules()
            format_spec = parse_format_string('{date:%m/%d/%Y},{description},{amount}')
            txns = parse_generic_csv(
                f.name,
                format_spec,
                rules
            )

            assert len(txns) == 3
            assert txns[0]['amount'] == 123.45
            assert txns[1]['amount'] == 5.99
            assert txns[2]['amount'] == 1234.56

            os.unlink(f.name)

    def test_european_format_csv(self):
        """Parse CSV with European number format."""
        # Note: CSV is still comma-delimited, but amounts use European format
        csv_content = """Date,Description,Amount
15.01.2025,GROCERY STORE,"123,45"
16.01.2025,COFFEE SHOP,"5,99"
17.01.2025,BIG PURCHASE,"1.234,56"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()

            rules = get_all_rules()
            format_spec = parse_format_string('{date:%d.%m.%Y},{description},{amount}')
            txns = parse_generic_csv(
                f.name,
                format_spec,
                rules,
                decimal_separator=','
            )

            assert len(txns) == 3
            assert txns[0]['amount'] == 123.45
            assert txns[1]['amount'] == 5.99
            assert txns[2]['amount'] == 1234.56

            os.unlink(f.name)

    def test_european_format_with_negative(self):
        """Parse European CSV with negative amounts (credits/refunds)."""
        csv_content = """Date,Description,Amount
15.01.2025,REFUND,"-500,00"
16.01.2025,PURCHASE,"250,00"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()

            rules = get_all_rules()
            format_spec = parse_format_string('{date:%d.%m.%Y},{description},{amount}')
            txns = parse_generic_csv(
                f.name,
                format_spec,
                rules,
                decimal_separator=','
            )

            assert len(txns) == 2
            # Negative amounts are preserved (credits/refunds)
            assert txns[0]['amount'] == -500.0
            assert txns[0]['is_credit'] == True
            # Positive amounts are expenses
            assert txns[1]['amount'] == 250.0
            assert txns[1]['is_credit'] == False

            os.unlink(f.name)

    def test_mixed_sources_different_separators(self):
        """Simulate mixed sources with different decimal separators."""
        # US format CSV
        us_csv = """Date,Description,Amount
01/15/2025,US STORE,100.50
"""
        # European format CSV (amounts quoted to handle comma)
        eu_csv = """Date,Description,Amount
15.01.2025,EU STORE,"100,50"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as us_f:
            us_f.write(us_csv)
            us_f.flush()

            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as eu_f:
                eu_f.write(eu_csv)
                eu_f.flush()

                rules = get_all_rules()

                # Parse US format
                us_format = parse_format_string('{date:%m/%d/%Y},{description},{amount}')
                us_txns = parse_generic_csv(
                    us_f.name,
                    us_format,
                    rules,
                    decimal_separator='.'
                )

                # Parse European format
                eu_format = parse_format_string('{date:%d.%m.%Y},{description},{amount}')
                eu_txns = parse_generic_csv(
                    eu_f.name,
                    eu_format,
                    rules,
                    decimal_separator=','
                )

                # Both should parse to same value
                assert us_txns[0]['amount'] == 100.50
                assert eu_txns[0]['amount'] == 100.50

                os.unlink(us_f.name)
                os.unlink(eu_f.name)
