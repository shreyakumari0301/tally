"""
Inline modifier parser for transaction matching rules.

Parses patterns like: COSTCO[amount>200][date=2025-01-15]
Extracts the regex pattern and conditions for amount/date matching.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, List


@dataclass
class AmountCondition:
    """Condition for matching transaction amounts."""
    operator: str  # '>', '<', '=', ':'
    value: Optional[float] = None
    min_value: Optional[float] = None  # For range operator
    max_value: Optional[float] = None  # For range operator


@dataclass
class DateCondition:
    """Condition for matching transaction dates."""
    operator: str  # '=', ':', 'month', 'relative'
    value: Optional[date] = None  # For exact match
    start_date: Optional[date] = None  # For range
    end_date: Optional[date] = None  # For range
    month: Optional[int] = None  # For month= modifier
    relative_days: Optional[int] = None  # For last30days


@dataclass
class ParsedPattern:
    """A pattern with optional inline modifiers extracted."""
    regex_pattern: str
    amount_conditions: List[AmountCondition] = field(default_factory=list)
    date_conditions: List[DateCondition] = field(default_factory=list)
    not_travel: bool = False  # If True, this pattern explicitly marks transaction as NOT travel


class ModifierParseError(ValueError):
    """Error parsing inline modifiers."""
    pass


# Regex patterns for parsing modifiers
# Only match modifiers at the END of the pattern string
# Must start with known keywords to avoid confusion with regex char classes like [A-Z]
MODIFIER_BLOCK_PATTERN = re.compile(r'\[(amount|date|month|not_travel)([^\]]*)\]')

# Individual modifier value patterns
AMOUNT_GT = re.compile(r'^\s*>\s*([\d.]+)\s*$')
AMOUNT_LT = re.compile(r'^\s*<\s*([\d.]+)\s*$')
AMOUNT_EQ = re.compile(r'^\s*=\s*([\d.]+)\s*$')
AMOUNT_GTE = re.compile(r'^\s*>=\s*([\d.]+)\s*$')
AMOUNT_LTE = re.compile(r'^\s*<=\s*([\d.]+)\s*$')
AMOUNT_RANGE = re.compile(r'^\s*:\s*([\d.]+)\s*-\s*([\d.]+)\s*$')

DATE_EQ = re.compile(r'^\s*=\s*(\d{4}-\d{2}-\d{2})\s*$')
DATE_RANGE = re.compile(r'^\s*:\s*(\d{4}-\d{2}-\d{2})\s*\.\.\s*(\d{4}-\d{2}-\d{2})\s*$')
DATE_RELATIVE = re.compile(r'^\s*:\s*last(\d+)days\s*$', re.IGNORECASE)

MONTH_EQ = re.compile(r'^\s*=\s*(\d{1,2})\s*$')


def parse_pattern_with_modifiers(pattern_str: str) -> ParsedPattern:
    """
    Parse a pattern string with optional inline modifiers.

    Examples:
        'COSTCO' -> ParsedPattern(regex='COSTCO', [], [])
        'COSTCO[amount>100]' -> ParsedPattern with amount condition
        'COSTCO(?!GAS)[amount:50-200][date:2025-01-01..2025-12-31]'

    Args:
        pattern_str: The pattern string, possibly with inline modifiers

    Returns:
        ParsedPattern with extracted regex and conditions

    Raises:
        ModifierParseError: If modifier syntax is invalid
    """
    if not pattern_str:
        return ParsedPattern(regex_pattern='', amount_conditions=[], date_conditions=[])

    amount_conditions = []
    date_conditions = []
    not_travel_flag = False

    # Find all modifier blocks and their positions
    # We need to identify which [...] blocks are modifiers vs regex char classes
    # Strategy: scan from the end, looking for [amount...], [date...], [month...], [not_travel]

    remaining = pattern_str

    # Work backwards from end to find modifier blocks
    while True:
        # Look for modifier pattern at the end
        match = None
        for m in MODIFIER_BLOCK_PATTERN.finditer(remaining):
            # Keep the last match
            match = m

        if match is None or match.end() != len(remaining):
            # No modifier at the end, we're done
            break

        keyword = match.group(1).lower()
        value_part = match.group(2)

        try:
            if keyword == 'amount':
                cond = _parse_amount_modifier(value_part)
                amount_conditions.insert(0, cond)  # Insert at front since we're going backwards
            elif keyword == 'date':
                cond = _parse_date_modifier(value_part)
                date_conditions.insert(0, cond)
            elif keyword == 'month':
                cond = _parse_month_modifier(value_part)
                date_conditions.insert(0, cond)
            elif keyword == 'not_travel':
                # [not_travel] modifier - no value part needed
                if value_part.strip():
                    raise ModifierParseError(f"Invalid not_travel modifier: [not_travel{value_part}]. Use [not_travel] with no value.")
                not_travel_flag = True
        except ModifierParseError:
            raise
        except Exception as e:
            raise ModifierParseError(f"Invalid modifier syntax: [{keyword}{value_part}] - {e}")

        # Remove this modifier from the remaining pattern
        remaining = remaining[:match.start()]

    return ParsedPattern(
        regex_pattern=remaining,
        amount_conditions=amount_conditions,
        date_conditions=date_conditions,
        not_travel=not_travel_flag
    )


def _parse_amount_modifier(value_part: str) -> AmountCondition:
    """Parse the value part of an amount modifier."""
    # Try each pattern
    m = AMOUNT_GT.match(value_part)
    if m:
        return AmountCondition(operator='>', value=float(m.group(1)))

    m = AMOUNT_GTE.match(value_part)
    if m:
        return AmountCondition(operator='>=', value=float(m.group(1)))

    m = AMOUNT_LT.match(value_part)
    if m:
        return AmountCondition(operator='<', value=float(m.group(1)))

    m = AMOUNT_LTE.match(value_part)
    if m:
        return AmountCondition(operator='<=', value=float(m.group(1)))

    m = AMOUNT_EQ.match(value_part)
    if m:
        return AmountCondition(operator='=', value=float(m.group(1)))

    m = AMOUNT_RANGE.match(value_part)
    if m:
        return AmountCondition(
            operator=':',
            min_value=float(m.group(1)),
            max_value=float(m.group(2))
        )

    raise ModifierParseError(
        f"Invalid amount modifier: [amount{value_part}]. "
        f"Expected: [amount>N], [amount<N], [amount=N], [amount>=N], [amount<=N], or [amount:MIN-MAX]"
    )


def _parse_date_modifier(value_part: str) -> DateCondition:
    """Parse the value part of a date modifier."""
    # Exact date: =2025-01-15
    m = DATE_EQ.match(value_part)
    if m:
        return DateCondition(
            operator='=',
            value=datetime.strptime(m.group(1), '%Y-%m-%d').date()
        )

    # Date range: :2025-01-01..2025-12-31
    m = DATE_RANGE.match(value_part)
    if m:
        return DateCondition(
            operator=':',
            start_date=datetime.strptime(m.group(1), '%Y-%m-%d').date(),
            end_date=datetime.strptime(m.group(2), '%Y-%m-%d').date()
        )

    # Relative: :last30days
    m = DATE_RELATIVE.match(value_part)
    if m:
        return DateCondition(
            operator='relative',
            relative_days=int(m.group(1))
        )

    raise ModifierParseError(
        f"Invalid date modifier: [date{value_part}]. "
        f"Expected: [date=YYYY-MM-DD], [date:YYYY-MM-DD..YYYY-MM-DD], or [date:lastNdays]"
    )


def _parse_month_modifier(value_part: str) -> DateCondition:
    """Parse the value part of a month modifier."""
    m = MONTH_EQ.match(value_part)
    if m:
        month = int(m.group(1))
        if not 1 <= month <= 12:
            raise ModifierParseError(f"Invalid month: {month}. Must be 1-12.")
        return DateCondition(operator='month', month=month)

    raise ModifierParseError(
        f"Invalid month modifier: [month{value_part}]. Expected: [month=1] to [month=12]"
    )


def evaluate_amount_condition(amount: float, condition: AmountCondition) -> bool:
    """
    Check if an amount satisfies the condition.

    Args:
        amount: The transaction amount (should be positive/absolute)
        condition: The amount condition to check

    Returns:
        True if the amount satisfies the condition
    """
    if condition.operator == '>':
        return amount > condition.value
    elif condition.operator == '>=':
        return amount >= condition.value
    elif condition.operator == '<':
        return amount < condition.value
    elif condition.operator == '<=':
        return amount <= condition.value
    elif condition.operator == '=':
        # Use epsilon for float comparison
        return abs(amount - condition.value) < 0.01
    elif condition.operator == ':':
        # Range is inclusive
        return condition.min_value <= amount <= condition.max_value
    return False


def evaluate_date_condition(txn_date: date, condition: DateCondition) -> bool:
    """
    Check if a date satisfies the condition.

    Args:
        txn_date: The transaction date
        condition: The date condition to check

    Returns:
        True if the date satisfies the condition
    """
    if condition.operator == '=':
        return txn_date == condition.value
    elif condition.operator == ':':
        return condition.start_date <= txn_date <= condition.end_date
    elif condition.operator == 'relative':
        cutoff = date.today() - timedelta(days=condition.relative_days)
        return txn_date >= cutoff
    elif condition.operator == 'month':
        return txn_date.month == condition.month
    return False


def check_all_conditions(
    parsed: ParsedPattern,
    amount: Optional[float],
    txn_date: Optional[date]
) -> bool:
    """
    Check if all conditions in a parsed pattern are satisfied.

    All conditions use AND logic - all must pass for the pattern to match.

    Args:
        parsed: The parsed pattern with conditions
        amount: Transaction amount (or None if not available)
        txn_date: Transaction date (or None if not available)

    Returns:
        True if all conditions pass (or if there are no conditions)
    """
    # Check amount conditions
    for cond in parsed.amount_conditions:
        if amount is None:
            return False  # Can't match if amount not provided
        if not evaluate_amount_condition(amount, cond):
            return False

    # Check date conditions
    for cond in parsed.date_conditions:
        if txn_date is None:
            return False  # Can't match if date not provided
        if not evaluate_date_condition(txn_date, cond):
            return False

    return True
