---
name: hledger
description: Plain-text double-entry accounting with hledger. Use when recording transactions, checking balances, generating financial reports (balance sheet, income statement, cashflow), importing CSV bank statements, budgeting, tracking time, managing multiple currencies, or doing year-end closing. Triggers on mentions of hledger, ledger-cli, journal files, double-entry accounting, balance assertions, or plain-text accounting.
---

# hledger

## Overview

hledger is a plain-text accounting tool implementing double-entry bookkeeping. You record transactions in a human-readable journal file, then query it for balance reports, income statements, cashflow, and more. Data stays in version-controllable text files — no database, no lock-in.

## Prerequisites

- `hledger` installed (`brew install hledger`, `apt install hledger`, or [hledger.org](https://hledger.org))
- Optional: `hledger-ui` (TUI), `hledger-web` (web UI)

## Journal Basics

### Transaction Format

```journal
2024-01-15 * (INV-042) Grocery store  ; tag:value
    expenses:food:groceries    $45.00
    assets:bank:checking
```

- **Date**: `YYYY-MM-DD`, `YYYY/MM/DD`, or `YYYY.MM.DD`
- **Status**: ` ` (unmarked), `!` (pending), `*` (cleared)
- **Code**: `(CODE)` in parentheses — check numbers, invoice IDs
- **Description**: free text, optionally split as `payee | note`
- **Postings**: indented lines with account name and optional amount
- **Comments**: `;` starts a comment; tags embedded as `name:value`

At least two postings per transaction. One amount may be omitted (inferred to balance).

### Account Names

Colon-separated hierarchy: `assets:bank:checking`, `expenses:food:groceries`. Five conventional top-level types:

| Type | Prefix | Normal Balance |
|------|--------|----------------|
| Asset | `assets:` | Debit (positive) |
| Liability | `liabilities:` | Credit (negative) |
| Equity | `equity:` | Credit |
| Revenue | `income:` or `revenue:` | Credit |
| Expense | `expenses:` | Debit |

Declare accounts for validation: `account assets:bank:checking  ; type:A`

### Amounts and Commodities

```journal
    expenses:food         $45.00        ; symbol left, no space
    expenses:travel       100.00 EUR    ; symbol right, with space
    assets:bank          -45.00 USD
```

- Commodity symbol position and spacing learned from first use or `commodity` directive
- Multiple commodities in one transaction require cost notation: `@ UNITPRICE` or `@@ TOTALPRICE`
- Balance assertions: `= $500.00` after amount (assert this account balance)

### Key Directives

| Directive | Example | Purpose |
|-----------|---------|---------|
| `account` | `account expenses:food  ; type:X` | Declare account (with optional type) |
| `commodity` | `commodity $1,000.00` | Declare display format |
| `P` | `P 2024-01-15 EUR $1.08` | Market price |
| `D` | `D $1,000.00` | Default commodity |
| `include` | `include 2024/*.journal` | Include files (supports globs) |
| `alias` | `alias savings = assets:bank:savings` | Account name alias |
| `~` | `~ monthly\n    (expenses:rent)  $1200` | Periodic rule (budgets/forecast) |
| `=` | `= ^income\n    (liabilities:tax)  *.33` | Auto posting rule |

## Essential Commands

| Command | Alias | Purpose |
|---------|-------|---------|
| `hledger print` | | Show journal entries |
| `hledger balance` | `bal` | Show account balances |
| `hledger register` | `reg` | Show postings with running total |
| `hledger aregister` | `areg` | Account register (bank-statement view) |
| `hledger balancesheet` | `bs` | Assets and liabilities |
| `hledger incomestatement` | `is` | Revenue and expenses |
| `hledger cashflow` | `cf` | Changes in liquid assets |
| `hledger accounts` | | List account names |
| `hledger import` | | Import CSV with duplicate detection |
| `hledger check` | | Run correctness checks |
| `hledger close` | | Year-end closing transactions |
| `hledger stats` | | Journal statistics |
| `hledger roi` | | Return on investment (IRR/TWR) |

## Common Workflows

### Check Balances

```bash
hledger bal                          # all account balances
hledger bal assets liabilities       # filter by account pattern
hledger bs                           # balance sheet
hledger is -M                        # monthly income statement
hledger cf -Q                        # quarterly cashflow
```

### View Transactions

```bash
hledger print                        # all transactions
hledger reg expenses -M              # monthly expense register
hledger areg assets:bank:checking    # bank statement view
hledger areg checking -H             # with historical running balance
```

### Filtering and Queries

```bash
hledger bal date:thismonth           # current month
hledger reg desc:grocery             # by description
hledger bal tag:project=alpha        # by tag
hledger bal amt:'>100'               # amounts over 100
hledger bal cur:EUR                  # EUR amounts only
hledger bal depth:2                  # top 2 account levels
hledger bal not:expenses:food        # exclude pattern
```

Query terms are AND'd by default. Multiple account patterns are OR'd.

### Multi-Period Reports

```bash
hledger bal -M                       # monthly
hledger bal -Q                       # quarterly
hledger bal -Y                       # yearly
hledger bal -p 'monthly from 2024'   # custom period
hledger bal -M --tree                # hierarchical
hledger bal -M -S                    # sorted by amount
hledger bal -M -T -A                 # with row totals and averages
```

### CSV Import

```bash
# Create rules file for your bank format
hledger import bank-download.csv --rules bank.csv.rules --dry-run
hledger import bank-download.csv --rules bank.csv.rules
```

Rules file example (`bank.csv.rules`):
```
skip 1
fields date, description, amount
date-format %m/%d/%Y
currency $
account1 assets:bank:checking

if grocery|supermarket
  account2 expenses:food:groceries

if salary|payroll
  account2 income:salary
```

See [references/csv-import.md](references/csv-import.md) for complete rules syntax.

### Multi-Currency

```journal
2024-03-01 * Buy euros
    assets:bank:eur       €500 @@ $540
    assets:bank:usd

P 2024-03-15 EUR $1.09
```

```bash
hledger bal -B                       # at cost (purchase price)
hledger bal -V                       # at market value (period end)
hledger bal -X USD                   # convert everything to USD
hledger bal --infer-market-prices    # infer prices from costs
```

### Budgeting

Define budget goals with periodic transaction rules:

```journal
~ monthly
    (expenses:food)         $500
    (expenses:rent)        $1200
    (expenses:transport)    $150
```

```bash
hledger bal --budget -M              # monthly budget comparison
hledger bal --budget -M -E           # include zero/unbudgeted
```

Output shows `ACTUAL [PERCENT% of GOAL]` per cell.

### Year-End Closing

```bash
hledger close --clopen -e 2025       # closing + opening transactions
hledger close --retain -e 2025       # retained earnings
hledger close --assert               # generate balance assertions
```

### Checks and Validation

```bash
hledger check                        # basic checks (parseable, balanced, assertions)
hledger check -s                     # strict (also: accounts, commodities declared)
hledger check ordereddates payees    # specific checks
```

Available checks: `parseable`, `autobalanced`, `assertions`, `balanced`, `commodities`, `accounts`, `ordereddates`, `payees`, `tags`, `recentassertions`, `uniqueleafnames`.

## Output Formats

Most report commands support:

```bash
hledger bal -O csv                   # CSV output
hledger bal -O json                  # JSON output
hledger bal -O html                  # HTML output
hledger bal -o report.csv            # format inferred from extension
```

Formats: `txt` (default), `csv`, `tsv`, `json`, `html`, `fods`. `print` also supports `beancount` and `sql`.

## Report Display Options

| Flag | Description |
|------|-------------|
| `-T` / `--tree` | Hierarchical account display |
| `-F` / `--flat` | Flat account list (default) |
| `--depth N` | Limit account depth |
| `-E` / `--empty` | Show zero-balance items |
| `-S` / `--sort-amount` | Sort by amount |
| `-N` / `--no-total` | Hide grand total |
| `-A` / `--average` | Show row averages |
| `--layout=wide\|tall\|bare\|tidy` | Multi-commodity layout |
| `--pretty` | Box-drawing characters |
| `-H` / `--historical` | Historical end balances (vs period changes) |
| `--invert` | Flip all amount signs |

## Configuration File

`hledger.conf` (searched in current dir, parent dirs, then `~/.hledger.conf`):

```conf
--pretty
--infer-costs
--infer-market-prices

[print]
--explicit
--show-costs

[web]
--port 5050
--allow edit
```

Disable with `--no-conf` or `-n`.

## Time Tracking

### Timedot format (`.timedot`)
```timedot
2024-03-15
fos.haskell   .... ..    ; 1.5h (each dot = 0.25h)
biz.research  .          ; 0.25h
inc.client1   3          ; 3h
```

### Timeclock format (`.timeclock`)
```timeclock
i 2024-03-15 09:00:00 client1:development
o 2024-03-15 12:30:00
i 2024-03-15 13:30:00 client1:meetings
o 2024-03-15 15:00:00
```

```bash
hledger -f time.timedot bal          # time totals by account
hledger -f time.timedot reg -D       # daily time register
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "transaction is unbalanced" | Check amounts sum to zero; use `@` for currency conversion |
| "balance assertion failed" | Use `hledger print` to check actual balance; use `=*` for inclusive assertions |
| "undeclared account" | Add `account` directive or remove `--strict` |
| "unknown commodity" | Add `commodity` directive or remove `--strict` |
| Amounts look wrong | Check `decimal-mark` directive; `1,000` may be parsed as 1.000 |
| CSV import duplicates | Use `hledger import` (not `print`); check `.latest` files |
| "could not parse date" | Check `date-format` in CSV rules matches your bank's format |

## Advanced Topics

For comprehensive reference documentation, see:

- [references/commands.md](references/commands.md) — Full command reference with all flags
- [references/journal-format.md](references/journal-format.md) — Complete journal syntax and directives
- [references/queries.md](references/queries.md) — Query language, smart dates, periods
- [references/csv-import.md](references/csv-import.md) — CSV rules file format and import workflow
- [references/reports.md](references/reports.md) — Report types, valuation, custom formatting
- [references/budgeting.md](references/budgeting.md) — Budgeting, time tracking, ROI, year-end
