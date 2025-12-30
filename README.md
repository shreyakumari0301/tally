# Tally

**A local rule engine for transaction classification.** Pair it with an LLM to eliminate the manual work.

Works with Claude Code, Codex, Copilot, Cursor, or a local model.

👉 **[Website](https://tallyai.money)** · **[Releases](https://github.com/davidfowl/tally/releases)**

## Install

**Linux/macOS:**
```bash
curl -fsSL https://tallyai.money/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://tallyai.money/install.ps1 | iex
```

**With uv:**
```bash
uv tool install git+https://github.com/davidfowl/tally
```

## Quick Start

```bash
tally init ./my-budget      # Create budget folder
cd my-budget
tally workflow              # See next steps
```

## Commands

| Command | Description |
|---------|-------------|
| `tally init [dir]` | Set up a new budget folder |
| `tally workflow` | Show next steps (detects setup state, unknown merchants) |
| `tally run` | Parse transactions and generate HTML report |
| `tally run --format json` | Output analysis as JSON with reasoning |
| `tally explain` | Explain why merchants are classified the way they are |
| `tally explain <merchant>` | Explain specific merchant's classification |
| `tally discover` | Find uncategorized transactions (`--format json` for LLMs) |
| `tally inspect <csv>` | Show CSV structure to build format string |
| `tally diag` | Debug config issues |
| `tally version` | Show version and check for updates |
| `tally update` | Update to latest version |

### Output Formats

Both `tally run` and `tally explain` support multiple output formats:

```bash
tally run --format json        # JSON with classification reasoning
tally run --format markdown    # Markdown report
tally run --format summary     # Text summary only
tally run -v                   # Verbose: include decision trace
tally run -vv                  # Very verbose: include thresholds, CV values
```

### Filtering

Filter output to specific classifications or categories:

```bash
tally run --format json --only monthly,variable   # Just these classifications
tally run --format json --category Food           # Just Food category
tally explain --classification monthly            # Explain all monthly merchants
tally explain --category Subscriptions            # Explain all subscriptions
```

### Category View

The HTML report includes a **Category View** section that organizes spending by category instead of by classification (monthly, annual, etc.). This provides an alternative perspective on your spending:

- **Grouping**: All transactions grouped by category (Food, Shopping, Bills, etc.)
- **Merchants**: See all merchants within each category, regardless of classification
- **Details**: Click to expand categories and see individual merchants and transactions
- **Percentages**: Shows what percentage of total spending each category represents

The category breakdown also appears in the text summary when running `tally run --summary`.

**Example Output:**
```
SPENDING BY CATEGORY
==================
Category              Total      % of Total
--------------------------------------------------
Food               $2,450.00       35.2%
Shopping           $1,820.00       26.1%
Bills              $1,200.00       17.2%
Transport            $890.00       12.8%
...
```

## Configuration

### settings.yaml

```yaml
year: 2025
currency_format: "€{amount}"  # Optional: €1,234 or "{amount} zł" for 1,234 zł

data_sources:
  - name: AMEX
    file: data/amex.csv
    type: amex
  - name: Chase
    file: data/chase.csv
    format: "{date:%m/%d/%Y},{description},{amount}"
  - name: BofA Checking
    file: data/bofa.csv
    format: "{date:%m/%d/%Y},{description},{-amount}"
  - name: German Bank
    file: data/german.csv
    format: "{date:%d.%m.%Y},{description},{amount}"
    decimal_separator: ","  # European format (1.234,56)
```

### Format Strings

| Token | Description |
|-------|-------------|
| `{date:%m/%d/%Y}` | Date with format |
| `{description}` | Transaction description |
| `{amount}` | Amount (positive = expense) |
| `{-amount}` | Negated amount (for banks where negative = expense) |
| `{_}` | Skip column |
| `{custom_name}` | Capture column for use in description template |

**Multi-column descriptions** - Some banks split info across columns:
```yaml
- name: European Bank
  file: data/bank.csv
  format: "{date:%d.%m.%Y},{_},{txn_type},{vendor},{_},{amount}"
  columns:
    description: "{vendor} ({txn_type})"  # Combines into "STORE NAME (Card payment)"
```

### merchant_categories.csv

```csv
Pattern,Merchant,Category,Subcategory,Tags
WHOLEFDS,Whole Foods,Food,Grocery,
UBER\s(?!EATS),Uber,Transport,Rideshare,business|reimbursable
UBER\s*EATS,Uber Eats,Food,Delivery,
NETFLIX,Netflix,Subscriptions,Streaming,entertainment|recurring
GITHUB,GitHub,Subscriptions,Software,business|recurring
COSTCO[amount>200],Costco Bulk,Shopping,Bulk,
```

Patterns are Python regex (case-insensitive). First match wins.

**Tags** are optional, pipe-separated labels for filtering:
- Use cases: `business`, `reimbursable`, `entertainment`, `recurring`, `tax-deductible`
- Filter in UI: Click tag badges or type `t:business` in search
- Filter in CLI: `tally explain --tags business,reimbursable`

**Inline modifiers** target specific transactions:
- `[amount>200]`, `[amount:50-100]` - Amount conditions
- `[date=2025-01-15]`, `[month=12]` - Date conditions

## For AI Agents

Run `tally workflow` at any time to see context-aware instructions:

```bash
tally workflow    # Shows next steps based on current state
```

The workflow command detects your setup state and shows relevant instructions:
- No config? → How to initialize
- No data sources? → How to configure them
- Unknown merchants? → Categorization workflow

**Key commands for agents:**
- `tally discover --format json` - Get unknown merchants with suggested patterns
- `tally run --format json -v` - Full analysis with classification reasoning
- `tally explain <merchant> -vv` - Why a merchant is classified (with rule info)
- `tally diag --format json` - Debug configuration issues

## Development Builds

Get the latest build from main branch:

**Update existing install:**
```bash
tally update --prerelease
```

**Fresh install (Linux/macOS):**
```bash
curl -fsSL https://tallyai.money/install.sh | bash -s -- --prerelease
```

**Fresh install (Windows):**
```powershell
iex "& { $(irm https://tallyai.money/install.ps1) } -Prerelease"
```

Dev builds are created automatically on every push to main. When running a dev version, `tally version` will notify you of newer dev builds.

## License

MIT
