## Implementation Complete ✅

I've expanded the `tally explain` command to address both requirements:

### 1. Show Raw Description Variations

When explaining a merchant, the command now displays all raw description variations that matched:

```bash
tally explain Netflix
```

**Output:**
```
Netflix -> Monthly
  Raw descriptions (3 variations):
    • NETFLIX.COM
    • NETFLIX*STREAMING
    • NETFLIX MONTHLY
  ...
```

This helps users identify when multiple services or locations are being grouped together under one merchant name.

### 2. Explain Specific Transactions

Added support for explaining specific transactions using the `--date` flag:

```bash
tally explain "STARBUCKS STORE 123" --date 2025-01-15
```

**Output:**
```
Transaction: STARBUCKS STORE 123
  Date: 2025-01-15
  Amount: $5.50
  Merchant: Starbucks
  Category: Food > Coffee
  Location: WA
  Travel: No
  Source: AMEX

  Rule: STARBUCKS.* (built-in)
```

This shows:
- Raw description
- Detected location
- Category and subcategory
- Which rule matched
- Travel status
- Source

### Implementation Details

**Changes:**
- ✅ Added `raw_descriptions` set tracking in `analyze_transactions()` to collect all raw description variations per merchant
- ✅ Updated `_print_merchant_explanation()` to display raw descriptions in text, JSON, and markdown formats
- ✅ Added `--date` argument to explain command parser
- ✅ Added `_print_transaction_explanation()` function for transaction-specific explanations
- ✅ Added transaction filtering logic in `cmd_explain()` to match by raw description and date
- ✅ Comprehensive tests (3 passing)
- ✅ Updated README with examples

**Files Modified:**
- `src/tally/analyzer.py` - Raw description tracking
- `src/tally/cli.py` - Enhanced explain command
- `tests/test_expand_explain.py` - Tests
- `README.md` - Documentation

**Usage Examples:**

```bash
# Show merchant with raw description variations
tally explain Netflix

# Explain specific transaction
tally explain "MERCHANT_RAW_DESC" --date 2025-04-30

# JSON output
tally explain Netflix --format json

# Verbose mode with full details
tally explain "STARBUCKS STORE 123" --date 2025-01-15 -v
```

All tests pass and the feature is ready for review! 🚀

