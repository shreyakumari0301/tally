"""Tests for transaction-level expression matching."""

import pytest
from datetime import date
from tally.expr_parser import (
    TransactionContext,
    TransactionEvaluator,
    matches_transaction,
    evaluate_transaction,
    parse_expression,
    ExpressionError,
)


class TestTransactionContext:
    """Tests for TransactionContext creation and properties."""

    def test_basic_context(self):
        """Context stores basic properties."""
        ctx = TransactionContext(
            description="NETFLIX STREAMING",
            amount=15.99,
            date=date(2025, 1, 15),
        )
        assert ctx.description == "NETFLIX STREAMING"
        assert ctx.amount == 15.99
        assert ctx.month == 1
        assert ctx.year == 2025
        assert ctx.day == 15

    def test_amount_absolute_value(self):
        """Amount is always positive."""
        ctx = TransactionContext(amount=-99.50)
        assert ctx.amount == 99.50

    def test_from_transaction_dict(self):
        """Create context from transaction dictionary."""
        txn = {
            'description': 'AMAZON PURCHASE',
            'amount': -45.00,
            'date': date(2025, 12, 25),
        }
        ctx = TransactionContext.from_transaction(txn)
        assert ctx.description == 'AMAZON PURCHASE'
        assert ctx.amount == 45.00
        assert ctx.month == 12
        assert ctx.year == 2025
        assert ctx.day == 25

    def test_from_transaction_with_raw_description(self):
        """Falls back to raw_description if description not present."""
        txn = {
            'raw_description': 'RAW DESC',
            'amount': 10.00,
        }
        ctx = TransactionContext.from_transaction(txn)
        assert ctx.description == 'RAW DESC'

    def test_no_date(self):
        """Date components are 0 when no date provided."""
        ctx = TransactionContext(description="TEST")
        assert ctx.month == 0
        assert ctx.year == 0
        assert ctx.day == 0


class TestContainsFunction:
    """Tests for the contains() function."""

    def test_contains_match(self):
        """contains() finds substring."""
        txn = {'description': 'NETFLIX.COM STREAMING', 'amount': 15.99}
        assert matches_transaction('contains("NETFLIX")', txn)
        assert matches_transaction('contains("netflix")', txn)  # case insensitive
        assert matches_transaction('contains("STREAMING")', txn)

    def test_contains_no_match(self):
        """contains() returns False when not found."""
        txn = {'description': 'AMAZON PURCHASE', 'amount': 45.00}
        assert not matches_transaction('contains("NETFLIX")', txn)

    def test_contains_with_and(self):
        """contains() works with boolean AND."""
        txn = {'description': 'UBER EATS ORDER', 'amount': 25.00}
        assert matches_transaction('contains("UBER") and contains("EATS")', txn)
        assert not matches_transaction('contains("UBER") and contains("RIDES")', txn)

    def test_contains_with_not(self):
        """contains() works with NOT."""
        txn = {'description': 'UBER RIDES', 'amount': 15.00}
        assert matches_transaction('contains("UBER") and not contains("EATS")', txn)


class TestRegexFunction:
    """Tests for the regex() function."""

    def test_regex_simple(self):
        """Basic regex matching."""
        txn = {'description': 'NETFLIX.COM', 'amount': 15.99}
        assert matches_transaction('regex("NETFLIX")', txn)
        assert matches_transaction('regex("NET.*COM")', txn)

    def test_regex_negative_lookahead(self):
        """Regex with negative lookahead for Uber vs Uber Eats."""
        uber_rides = {'description': 'UBER TRIP', 'amount': 25.00}
        uber_eats = {'description': 'UBER EATS ORDER', 'amount': 30.00}

        # Match Uber but exclude if EATS appears anywhere
        expr = r'regex("UBER(?!.*EATS)")'
        assert matches_transaction(expr, uber_rides)
        assert not matches_transaction(expr, uber_eats)

    def test_regex_case_insensitive(self):
        """Regex is case insensitive."""
        txn = {'description': 'Netflix Streaming', 'amount': 15.99}
        assert matches_transaction('regex("NETFLIX")', txn)
        assert matches_transaction('regex("netflix")', txn)

    def test_regex_invalid_pattern(self):
        """Invalid regex raises error."""
        txn = {'description': 'TEST', 'amount': 10.00}
        with pytest.raises(ExpressionError, match="Invalid regex pattern"):
            matches_transaction('regex("[invalid")', txn)


class TestAmountConditions:
    """Tests for amount-based conditions."""

    def test_amount_greater_than(self):
        """amount > threshold."""
        txn = {'description': 'PURCHASE', 'amount': 150.00}
        assert matches_transaction('amount > 100', txn)
        assert not matches_transaction('amount > 200', txn)

    def test_amount_less_than(self):
        """amount < threshold."""
        txn = {'description': 'PURCHASE', 'amount': 50.00}
        assert matches_transaction('amount < 100', txn)
        assert not matches_transaction('amount < 25', txn)

    def test_amount_range(self):
        """amount in range."""
        txn = {'description': 'PURCHASE', 'amount': 75.00}
        assert matches_transaction('amount >= 50 and amount <= 100', txn)
        assert not matches_transaction('amount >= 100 and amount <= 200', txn)

    def test_negative_amount_becomes_positive(self):
        """Negative amounts are converted to positive."""
        txn = {'description': 'PURCHASE', 'amount': -150.00}
        assert matches_transaction('amount > 100', txn)
        assert matches_transaction('amount == 150', txn)


class TestDateConditions:
    """Tests for date-based conditions."""

    def test_month_equals(self):
        """month == number."""
        txn = {'description': 'PURCHASE', 'amount': 100, 'date': date(2025, 12, 15)}
        assert matches_transaction('month == 12', txn)
        assert not matches_transaction('month == 1', txn)

    def test_year_equals(self):
        """year == number."""
        txn = {'description': 'PURCHASE', 'amount': 100, 'date': date(2025, 6, 1)}
        assert matches_transaction('year == 2025', txn)
        assert not matches_transaction('year == 2024', txn)

    def test_day_equals(self):
        """day == number."""
        txn = {'description': 'PURCHASE', 'amount': 100, 'date': date(2025, 1, 25)}
        assert matches_transaction('day == 25', txn)

    def test_date_comparison(self):
        """date >= "YYYY-MM-DD" comparison."""
        txn = {'description': 'PURCHASE', 'amount': 100, 'date': date(2025, 6, 15)}
        assert matches_transaction('date >= "2025-01-01"', txn)
        assert matches_transaction('date <= "2025-12-31"', txn)
        assert not matches_transaction('date < "2025-06-01"', txn)

    def test_date_range(self):
        """Date range for Black Friday example."""
        black_friday = {'description': 'BESTBUY', 'amount': 500, 'date': date(2025, 11, 29)}
        regular_day = {'description': 'BESTBUY', 'amount': 500, 'date': date(2025, 7, 15)}

        expr = 'date >= "2025-11-28" and date <= "2025-11-30"'
        assert matches_transaction(expr, black_friday)
        assert not matches_transaction(expr, regular_day)

    def test_invalid_date_format(self):
        """Invalid date format raises error."""
        txn = {'description': 'TEST', 'amount': 10, 'date': date(2025, 1, 1)}
        with pytest.raises(ExpressionError, match="Invalid date format"):
            matches_transaction('date >= "01/01/2025"', txn)


class TestCombinedExpressions:
    """Tests for complex combined expressions."""

    def test_contains_and_amount(self):
        """Pattern + amount condition."""
        small_costco = {'description': 'COSTCO #123', 'amount': 75.00}
        large_costco = {'description': 'COSTCO #123', 'amount': 250.00}

        expr = 'contains("COSTCO") and amount > 200'
        assert not matches_transaction(expr, small_costco)
        assert matches_transaction(expr, large_costco)

    def test_pattern_month_amount(self):
        """Pattern + month + amount for holiday gifts."""
        holiday_gift = {'description': 'AMAZON', 'amount': 150, 'date': date(2025, 12, 10)}
        regular = {'description': 'AMAZON', 'amount': 150, 'date': date(2025, 6, 10)}
        small_holiday = {'description': 'AMAZON', 'amount': 25, 'date': date(2025, 12, 10)}

        expr = 'contains("AMAZON") and month == 12 and amount > 100'
        assert matches_transaction(expr, holiday_gift)
        assert not matches_transaction(expr, regular)
        assert not matches_transaction(expr, small_holiday)

    def test_or_conditions(self):
        """OR conditions."""
        netflix = {'description': 'NETFLIX', 'amount': 15.99}
        spotify = {'description': 'SPOTIFY', 'amount': 9.99}
        amazon = {'description': 'AMAZON', 'amount': 45.00}

        expr = 'contains("NETFLIX") or contains("SPOTIFY")'
        assert matches_transaction(expr, netflix)
        assert matches_transaction(expr, spotify)
        assert not matches_transaction(expr, amazon)


class TestVariables:
    """Tests for user-defined variables."""

    def test_variable_in_expression(self):
        """Variables can be used in expressions."""
        txn = {'description': 'PURCHASE', 'amount': 600}
        variables = {'is_large': True, 'threshold': 500}

        # Using variable as condition
        assert matches_transaction('is_large', txn, variables)
        assert matches_transaction('amount > threshold', txn, variables)

    def test_computed_variable(self):
        """Pre-computed variable values."""
        txn = {'description': 'AMAZON', 'amount': 150, 'date': date(2025, 12, 1)}
        # Simulate pre-computed: is_holiday_season = month >= 11 and month <= 12
        variables = {'is_holiday_season': True}

        expr = 'contains("AMAZON") and is_holiday_season'
        assert matches_transaction(expr, txn, variables)


class TestInOperator:
    """Tests for the 'in' operator with strings."""

    def test_string_in_description(self):
        """'X' in description (case insensitive)."""
        txn = {'description': 'NETFLIX STREAMING SERVICE', 'amount': 15.99}
        assert matches_transaction('"NETFLIX" in description', txn)
        assert matches_transaction('"netflix" in description', txn)
        assert matches_transaction('"STREAMING" in description', txn)
        assert not matches_transaction('"AMAZON" in description', txn)

    def test_not_in_description(self):
        """'X' not in description."""
        txn = {'description': 'UBER RIDES', 'amount': 25.00}
        assert matches_transaction('"EATS" not in description', txn)
        assert not matches_transaction('"UBER" not in description', txn)
