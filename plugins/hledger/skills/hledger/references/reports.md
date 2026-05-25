# hledger Reports Reference

Comprehensive reference for hledger's reporting commands, output formats, and display options.

## Report Types Overview

| Report | Command | Description |
|--------|---------|-------------|
| Balance | `bal` | Account balances (single or multi-period) |
| Register | `reg` | One line per posting with running total |
| Account Register | `areg` | One line per transaction for a specific account |
| Balance Sheet | `bs` | Assets + Liabilities (compound) |
| Income Statement | `is` | Revenue + Expenses (compound) |
| Cash Flow | `cf` | Cash account changes (compound) |
| Balance Sheet Equity | `bse` | Assets + Liabilities + Equity (compound) |

## Balance Report

Single-period (one column) or multi-period (tabular with `-p`, `-D`, `-W`, `-M`, `-Q`, `-Y`).

### Calculation Modes

| Flag | Mode | Description |
|------|------|-------------|
| `--sum` | Sum (default) | Sum of posting amounts |
| `--valuechange` | Value change | Change in period-end values |
| `--gain` | Gain | Unrealized capital gains |
| `--budget` | Budget | Actual vs budget goal comparison |
| `--count` | Count | Number of postings |

### Accumulation Modes

| Flag | Mode | Description |
|------|------|-------------|
| `--change` | Change (default single-period) | Net change within each period |
| `--cumulative` | Cumulative | Running total from report start |
| `-H`/`--historical` | Historical | Running total from journal start |

### Layout Options

| Layout | Description |
|--------|-------------|
| `wide[,W]` | Default. All commodities on one line. Optional elide width W |
| `tall` | One commodity per row |
| `bare` | Commodity in a separate column |
| `tidy` | One row per value (CSV/TSV only) |

Use `--layout=LAYOUT` to select.

### Examples

```bash
# Simple balances
hledger bal expenses

# Monthly expense breakdown
hledger bal expenses -M --tree

# Historical balances quarterly
hledger bal assets -Q -H

# Tall layout for multi-commodity
hledger bal --layout=tall

# Tidy CSV for data analysis
hledger bal -M -O csv --layout=tidy
```

## Register Report

One line per posting with a running total. Default accumulation: `--cumulative`.

### Key Flags

| Flag | Description |
|------|-------------|
| `-H`/`--historical` | Running total from journal start |
| `-A`/`--average` | Show running average |
| `-r`/`--related` | Show other postings in the same transaction |
| `-m`/`--match` | Find best match for a description (smart import) |
| `-w`/`--width` | Set output width |
| `--align-all` | Align all columns (not just amounts) |

### Sorting

`--sort=KEY[,KEY,...]` where keys are: `date`, `desc`/`description`, `account`, `amount`, `absamount`. Prefix `-` for descending.

```bash
# Sort by amount descending
hledger reg expenses --sort=-amount

# Sort by account then date
hledger reg --sort=account,date
```

### With Intervals

Adding interval flags (`-D`, `-W`, `-M`, `-Q`, `-Y`) produces summary postings per interval instead of individual postings.

```bash
# Monthly summary of expenses
hledger reg expenses -M

# Weekly income with running average
hledger reg income -W -A
```

## Account Register

One line per transaction for a single account. Bank-statement style view.

**Required argument**: account pattern (ACCTPAT).

Default accumulation: `-H` (historical running balance).

### Key Flags

| Flag | Description |
|------|-------------|
| `--txn-dates` | Use transaction dates instead of posting dates |
| `--no-elide` | Show full account names |
| `--invert` | Negate amounts |
| `-w`/`--width` | Set output width |

```bash
# Bank statement view
hledger areg checking

# Credit card with full names
hledger areg 'liabilities:credit' --no-elide

# Inverted view (positive = spending)
hledger areg expenses:food --invert
```

## Compound Reports

Multiple sub-reports rendered together with overall totals.

| Command | Sub-reports | Default Accumulation |
|---------|------------|---------------------|
| `bs` | Assets, Liabilities | `-H` (historical) |
| `is` | Revenue, Expenses | `--change` |
| `cf` | Cash accounts | `--change` |
| `bse` | Assets, Liabilities, Equity | `-H` (historical) |

### Shared Flags

All compound reports accept:

- Calculation: `--sum`, `--valuechange`, `--gain`, `--count`
- Accumulation: `--change`, `--cumulative`, `-H`
- Display: `-l`/`--flat`, `-t`/`--tree`, `--drop=N`, `--declared`
- Aggregation: `-A`/`--average`, `-T`/`--row-total`, `--summary-only`
- Suppression: `-N`/`--no-total`, `--no-elide`
- Sorting: `-S`/`--sort-amount`, `-%`/`--percent`
- Layout: `--layout=ARG`
- Format: `--format=FMTSTR`, `-O FMT`, `-o FILE`
- Other: `--base-url`

```bash
# Monthly balance sheet
hledger bs -M

# Income statement for Q1
hledger is -p 'jan-mar'

# Cash flow with percentages
hledger cf -M -%

# Balance sheet equity, flat with depth limit
hledger bse --flat --depth 2
```

## Budget Reports

Use `--budget[=DESCPAT]` with any balance command. Budget goals come from periodic transactions (`~` rules) in the journal.

Output format per cell: `ACTUAL [PERCENT% of GOAL]`.

```bash
# Compare actuals to all budgets
hledger bal --budget -M

# Budget for specific category
hledger bal --budget=groceries expenses:food -M

# Show unbudgeted accounts too
hledger bal --budget -M -E
```

### Periodic Transaction Syntax

```journal
~ monthly
    expenses:rent          $1500
    expenses:food          $600
    expenses:transport     $200
    budget:expenses

~ weekly
    expenses:coffee        $25
    budget:expenses
```

Key points:
- `-E` shows accounts with no budget or no activity
- Budget cells contain `(Maybe Actual, Maybe Goal)` internally
- Works with compound reports: `hledger bs --budget -M`

## Valuation

Convert amounts to cost basis or market value.

### Valuation Flags

| Flag | Description |
|------|-------------|
| `-B`/`--cost` | Convert to cost basis (using `@`/`@@` prices) |
| `-V`/`--market` | Convert to market value at period end |
| `-X COMM`/`--exchange COMM` | Convert to specified commodity at period end |
| `--value=TYPE[,COMM]` | Fine-grained control over valuation timing |

### --value Types

| Type | Description |
|------|-------------|
| `then` | Value at posting date |
| `end` | Value at period end (or report end) |
| `now` | Value at today's date |
| `DATE` | Value at specific date (YYYY-MM-DD) |

Append `,COMM` to convert to a specific commodity: `--value=end,USD`.

### Price Oracle

hledger finds conversion prices by searching the shortest path through a price graph. It searches forward prices first, then forward + reverse.

`--infer-market-prices` derives market prices from transaction costs (`@`/`@@` amounts).

### Restrictions

- `--valuechange` requires `--value=end`
- `--gain` cannot combine with `--cost`

```bash
# Cost basis
hledger bal investments -B

# Market value in USD
hledger bal -X USD

# Value at specific date
hledger bal investments --value=2025-12-31,USD

# Infer prices from transactions
hledger bal -V --infer-market-prices
```

## Output Formats

| Format | Flag | Supported By |
|--------|------|-------------|
| txt | `-O txt` | All reports |
| csv | `-O csv` | bal, reg, areg, print |
| tsv | `-O tsv` | bal, reg, areg, print |
| json | `-O json` | bal, reg, areg, print |
| html | `-O html` | bal, reg, areg |
| fods | `-O fods` | bal, reg, areg |
| beancount | `-O beancount` | print |
| sql | `-O sql` | print |

Select with `-O FMT` or by file extension with `-o FILE.ext`.

```bash
# CSV output
hledger bal -M -O csv

# Write to HTML file
hledger bal -M -o report.html

# JSON for programmatic use
hledger reg -O json

# Export to LibreOffice spreadsheet
hledger bal -M -o balances.fods
```

## Custom Format Strings

Customize text output with `--format=FMTSTR`.

### Syntax

```
%[ALIGNMENT][MINWIDTH][.MAXWIDTH](FIELDNAME)
```

### Alignment Prefixes

| Prefix | Position |
|--------|----------|
| `%^` | Top-aligned |
| `%_` | Bottom-aligned (default) |
| `%,` | One-line (squeeze multi-line to single) |
| `%-` | Left-justified |

### Available Fields

| Field | Description |
|-------|-------------|
| `account` | Account name |
| `total` | Amount/total |
| `depth_spacer` | Indentation for tree mode |
| `description` | Transaction description |
| `N` (numeric) | Nth field |

### Width Control

- `%20(total)` — minimum width 20
- `%.30(account)` — maximum width 30
- `%20.40(account)` — min 20, max 40

### Default Balance Format

```
%20(total)  %2(depth_spacer)%-(account)
```

```bash
# Custom balance format
hledger bal --format='%40(account)  %15(total)'

# Compact register
hledger reg --format='%-(account)  %12(amount)  %12(total)'
```

## Display Options

### Tree vs Flat

| Flag | Description |
|------|-------------|
| `--tree`/`-t` | Show accounts as a hierarchy |
| `--flat`/`-l` | Show accounts as flat list (default) |
| `--depth N` | Limit display depth |
| `--drop N` | Drop N leading account name components |

### Filtering What Shows

| Flag | Description |
|------|-------------|
| `--empty`/`-E` | Show zero-balance accounts |
| `--declared` | Include accounts from directives even if unused |
| `--no-elide` | Show all parent accounts (don't skip boring ones) |

### Aggregation

| Flag | Description |
|------|-------------|
| `--average`/`-A` | Show running average column |
| `--row-total`/`-T` | Show row totals column (multi-period) |
| `--no-total`/`-N` | Hide the grand total row |
| `--summary-only` | Show only top-level totals |

### Sorting and Percentages

| Flag | Description |
|------|-------------|
| `--sort-amount`/`-S` | Sort by amount instead of account name |
| `--percent`/`-%` | Show percentage of column total |

### Other

| Flag | Description |
|------|-------------|
| `--invert` | Negate all amounts |
| `--transpose` | Swap rows and columns |
| `--show-costs` | Show cost amounts alongside |
| `--pretty` | Use unicode box-drawing characters |
| `--color` | Enable ANSI color output |

### Status Filters

| Flag | Description |
|------|-------------|
| `-U`/`--unmarked` | Show only unmarked transactions |
| `-P`/`--pending` | Show only pending (`!`) transactions |
| `-C`/`--cleared` | Show only cleared (`*`) transactions |

Combine any subset. All three or none = show all.

```bash
# Tree view with depth limit
hledger bal expenses --tree --depth 2

# Sorted by amount with percentages
hledger bal expenses -S -%

# Show empty accounts
hledger bal -E --declared

# Only cleared transactions
hledger bal -C
```
