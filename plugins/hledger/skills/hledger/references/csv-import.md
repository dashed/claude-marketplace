# CSV Import Reference

hledger can convert CSV (and TSV/SSV) files into journal entries using rules files that describe the mapping.

## CSV Import Workflow

1. Obtain CSV from bank/institution
2. Create a rules file (`.csv.rules`) describing the CSV format
3. Run `hledger import` or `hledger print -f data.csv` to generate transactions
4. Review and commit to journal

hledger auto-discovers rules files by name: for `bank.csv`, it looks for `bank.csv.rules` in the same directory.

## Rules File Directives

| Directive | Description |
|-----------|-------------|
| `fields` | Name CSV columns for field assignment |
| `skip` | Skip N header lines (`skip` alone = `skip 1`) |
| `separator` | Column separator: single char, `TAB`, or `SPACE` |
| `date-format` | strftime format for parsing dates (e.g., `%m/%d/%Y`) |
| `decimal-mark` | Decimal character: `.` or `,` |
| `encoding` | File encoding (e.g., `utf-8`, `latin1`) |
| `timezone` | Timezone for dates lacking one |
| `newest-first` | Records are in reverse chronological order |
| `intra-day-reversed` | Records within the same day are reversed |
| `balance-type` | Type of balance assertions: `totalchange`, `change` |
| `source` | Specify input file(s) or command |
| `archive` | Enable auto-archiving of imported files |
| `include` | Include another rules file |

## Fields Directive

Maps CSV columns to hledger fields by position:

```
fields date, description, amount, , balance
```

- Comma-separated, positional (first name = first CSV column)
- Empty names skip that column
- Case-insensitive
- Quoted names supported for columns with special characters

## Assignable Fields

### Transaction-level

| Field | Description |
|-------|-------------|
| `date` | Transaction date (required) |
| `date2` | Secondary date |
| `status` | Transaction status (`*`, `!`, or empty) |
| `code` | Transaction code (e.g., check number) |
| `description` | Transaction description/payee |
| `comment` | Transaction-level comment |

### Per-posting (numbered 1-99)

| Field Pattern | Description |
|---------------|-------------|
| `accountN` | Account name for posting N |
| `amountN` | Amount for posting N |
| `amountN-in` | Inflow amount for posting N (positive) |
| `amountN-out` | Outflow amount for posting N (positive) |
| `balanceN` | Balance assertion for posting N |
| `commentN` | Comment for posting N |
| `currencyN` | Currency symbol for posting N |

Unnumbered `amount`, `balance`, `currency` are aliases for `amount1`, `balance1`, `currency1`.

### Pseudo-fields

| Field | Description |
|-------|-------------|
| `skip` | Set to non-empty to skip this record |
| `end` | Set to non-empty to stop processing |

## Assignment Syntax

Assign values outside the `fields` directive:

```
account1 assets:bank:checking
currency $
description %2 - %3
```

Both `fieldname value` and `fieldname: value` forms work.

### CSV Field References

| Syntax | Meaning |
|--------|---------|
| `%fieldname` | Value of a named field |
| `%N` | Value of CSV column N (1-based) |
| `\1`, `\2` | Regex match groups from conditionals |

Interpolation combines references: `description %1 - %2`.

## Conditional Blocks

### Standard (matches whole record)

```
if PATTERN
 account2 expenses:food
```

Multiple patterns (OR logic):

```
if
PATTERN1
PATTERN2
 account2 expenses:food
```

### Field-specific

```
if %description PATTERN
 account2 expenses:food
```

### Conditional Tables

Compact multi-rule format:

```
if,account2,comment
PATTERN1,expenses:food,groceries
PATTERN2,expenses:transport,commute
PATTERN3,expenses:utilities,monthly bill
```

## Matcher Features

### Regex Matching

All patterns are case-insensitive regular expressions.

- **Record matchers**: regex matches against all CSV fields joined by commas
- **Field matchers**: `%fieldname REGEX` matches a specific field

### Boolean Operators

| Prefix | Meaning |
|--------|---------|
| (none) | OR — matches if any pattern matches |
| `&` or `&&` | AND — all prefixed patterns must match |
| `!` | NOT — pattern must not match |
| `&&!` | AND NOT — combined |

```
if
%description grocery
& %amount [0-9]{2}\.[0-9]{2}
 account2 expenses:food:grocery
```

### Match Groups

Capture groups from regex for use in assignments:

```
if %description (walmart|target|costco)(.*)
 account2 expenses:shopping
 comment store: \1, details: \2
```

## Source and Archive Rules

### Source

Specify where to read CSV data:

```
# Direct file
source ~/Downloads/bank.csv

# Glob pattern (newest file used)
source ~/Downloads/bank-statement*.csv

# Pipe through a command
source ~/Downloads/bank.csv | sed 's/foo/bar/'

# Generate data from a command
source | generate-csv.sh
```

Tilde (`~`) expansion is supported.

### Archive

Enable automatic archiving of imported files to a `data/` subdirectory:

```
archive
```

After import, source files are moved to `data/` next to the rules file.

## Import Command

```
hledger import [-f JOURNAL] CSVFILES...
```

### Flags

| Flag | Description |
|------|-------------|
| `-f JOURNAL` | Target journal file (default: `~/.hledger.journal`) |
| `--dry-run` | Preview what would be imported without writing |
| `--catchup` | Mark files as imported without actually importing |

### Duplicate Detection

hledger uses `.latest.FILENAME` files to track what has been imported:

- Stores the date(s) of the latest imported records
- On subsequent imports, only records newer than the stored date are imported
- First import: all records are imported

To initialize without importing (e.g., for an existing journal):

```bash
hledger import --catchup bank.csv
```

### Alternative: Print-based Import

```bash
hledger print --new -f bank.csv >> main.journal
```

## Common Rules File Patterns

### Simple Bank Checking (Date, Description, Amount)

```
# bank-checking.csv.rules
skip 1
date-format %m/%d/%Y
fields date, description, amount

account1 assets:bank:checking
currency $

if %amount ^-
 account2 expenses:unknown

if %amount ^[^-]
 account2 income:unknown

if %description (payroll|salary|direct.dep)
 account2 income:salary

if %description (amazon|amzn)
 account2 expenses:shopping

if %description (whole.foods|trader.joe|safeway|kroger)
 account2 expenses:food:grocery
```

### Bank with Separate Debit/Credit Columns

```
# bank-debit-credit.csv.rules
skip 1
date-format %Y-%m-%d
fields date, description, , debit, credit

account1 assets:bank:checking
currency $
amount-in %credit
amount-out %debit

if %description (rent|landlord)
 account2 expenses:housing:rent

if %description (electric|water|gas|utility)
 account2 expenses:utilities
```

### Credit Card Statement

```
# creditcard.csv.rules
skip 1
date-format %m/%d/%Y
fields date, , description, amount

account1 liabilities:creditcard:visa
currency $

# Payments to the card
if %description (payment|thank.you)
 account2 assets:bank:checking

# Common categories
if,account2
grocery|supermarket,expenses:food:grocery
restaurant|cafe|starbucks,expenses:food:dining
uber|lyft|taxi,expenses:transport
netflix|spotify|hulu,expenses:entertainment:subscriptions
amazon|amzn,expenses:shopping
```

### European Bank (Comma Decimals, Semicolons)

```
# euro-bank.csv.rules
skip 1
separator ;
decimal-mark ,
date-format %d.%m.%Y
fields date, description, , amount, balance

account1 assets:bank:sparkasse
currency EUR

balance1 %balance

if %description (miete|wohnung)
 account2 expenses:housing:rent

if %description (rewe|aldi|lidl|edeka)
 account2 expenses:food:grocery
```

### PayPal Export

```
# paypal.csv.rules
skip 1
date-format %m/%d/%Y
fields date, , description, currency, amount, , ,

account1 assets:online:paypal

if %amount ^-
 account2 expenses:paypal

if %amount ^[^-]
 account2 income:paypal

if %description (transfer.*bank|withdraw)
 account2 assets:bank:checking
```

### Investment / Brokerage Account

```
# brokerage.csv.rules
skip 1
date-format %Y-%m-%d
fields date, description, , amount, balance

account1 assets:investments:brokerage
currency $

if %description dividend
 account2 income:dividends

if %description (buy|purchase)
 account2 expenses:investments

if %description (sell|redemption)
 account2 income:capital-gains

if %description (fee|commission)
 account2 expenses:fees:brokerage
```
