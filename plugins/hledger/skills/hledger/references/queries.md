# hledger Query Language Reference

## Query Terms

Query terms filter transactions and postings. A bare pattern (no prefix) matches account names.

| Prefix | Target | Match Type |
|--------|--------|------------|
| `acct:REGEX` | Account names | Case-insensitive infix regex |
| `desc:REGEX` | Transaction description | Case-insensitive infix regex |
| `payee:REGEX` | Payee (before `\|` in description) | Case-insensitive infix regex |
| `note:REGEX` | Note (after `\|` in description) | Case-insensitive infix regex |
| `code:REGEX` | Transaction code | Case-insensitive infix regex |
| `tag:NAME[=VALUE]` | Tag name, optionally value | Regex match |
| `date:DATEQUERY` | Primary dates | Period expression syntax |
| `date2:DATEQUERY` | Secondary dates | Period expression syntax |
| `amt:AMTQUERY` | Posting amount | Numeric comparison |
| `cur:REGEX` | Commodity symbol | Full/anchored regex (`^...$`) |
| `status:VALUE` | Transaction status | See below |
| `real:BOOL` | Real vs virtual postings | `1`=real, `0`=virtual |
| `depth:N` | Account depth | Accounts at depth <= N |
| `type:CODES` | Account type | Type code letters |
| `not:TERM` | Negation | Negates any query term |
| `expr:EXPR` | Boolean expression | AND/OR/NOT with parens |
| `any:EXPR` | Any single posting matches | All sub-queries on one posting |
| `all:EXPR` | All postings match | Every posting satisfies |
| `inacct:REGEX` | Account (register reports) | Infix regex |
| `inacctonly:REGEX` | Account only (register) | Infix regex |

### Status Values

| Value | Meaning |
|-------|---------|
| `*` or `1` | Cleared |
| `!` | Pending |
| (empty) or `0` | Unmarked |

### Type Codes

| Code | Account Type |
|------|-------------|
| `A` | Asset |
| `L` | Liability |
| `E` | Equity |
| `R` | Revenue |
| `X` | Expense |
| `C` | Cash |
| `V` | Conversion |

## Amount Queries

The `amt:` prefix supports numeric comparisons with operators.

**Operators**: `<`, `<=`, `>`, `>=`, `=`, or bare number (equals).

**Signed vs unsigned behavior**:
- **Signed** (`+` or `-` prefix): Compares against the actual signed amount. `amt:>0` matches credits; `amt:<0` matches debits.
- **Unsigned** (non-zero, no sign prefix): Compares against absolute magnitude. `amt:>100` matches postings where |amount| > 100.

Examples:
```
amt:>1000       # absolute magnitude greater than 1000
amt:<-50        # signed amount less than -50 (debits exceeding 50)
amt:>=0         # signed: non-negative amounts
amt:=0          # exactly zero
```

## Query Combination Rules

When multiple query terms appear together:

1. Multiple **same-type** patterns are **OR'd** within each group:
   - Multiple `acct:` patterns → match any
   - Multiple `desc:` patterns → match any
   - Multiple `status:` patterns → match any

2. Different **groups** are **AND'd** together:
   - `acct:food desc:grocery` → account matches "food" AND description matches "grocery"

## Boolean Expressions

The `expr:` prefix enables full boolean logic.

**Operators** (case-insensitive):
- `NOT` — negate next term
- `AND` — both must match
- `OR` — either must match
- `(` `)` — grouping

**Precedence** (high to low): `NOT` > `AND` > `OR` > space (implicit AND)

Examples:
```
expr:"acct:food AND NOT acct:dining"
expr:"(acct:bank OR acct:cash) AND amt:>100"
expr:"desc:grocery OR desc:supermarket"
```

**Limitation**: `date:` cannot appear inside `OR` expressions (#2178).

### any: and all: Quantifiers

- `any:EXPR` — transaction matches if ANY single posting satisfies all sub-queries
- `all:EXPR` — transaction matches if ALL postings satisfy the expression

## Smart Dates

hledger accepts flexible date formats in queries, `--begin`, `--end`, and `--period`.

### Absolute Formats

| Format | Example | Notes |
|--------|---------|-------|
| `YYYY-MM-DD` | `2024-03-15` | ISO standard |
| `YYYY/MM/DD` | `2024/03/15` | Slash separator |
| `YYYY.MM.DD` | `2024.03.15` | Dot separator |
| `YYYYMMDD` | `20240315` | 8-digit compact |
| `YYYY-MM` | `2024-03` | First of month |
| `YYYY/MM` | `2024/03` | First of month |
| `YYYYMM` | `202403` | 6-digit compact |
| `YYYY` | `2024` | First of year |
| `MM/DD` | `03/15` | Current year |
| `DD` | `15` | Current month |
| monthname | `january`, `jan` | First of that month |

### Relative Formats

| Format | Example |
|--------|---------|
| `today` | Current date |
| `yesterday` | Previous day |
| `tomorrow` | Next day |
| `this day/week/month/quarter/year` | Current period start |
| `last day/week/month/quarter/year` | Previous period start |
| `next day/week/month/quarter/year` | Next period start |
| `in N days/weeks/months/quarters/years` | N periods from now |
| `N days/weeks/months/quarters/years ago` | N periods before now |
| `N days/weeks/months/quarters/years ahead` | N periods from now |
| `in -N days/weeks/...` | Negative offset (same as ago) |

## Date Span Syntax

Date spans define inclusive start and exclusive end boundaries.

| Syntax | Meaning |
|--------|---------|
| `DATE..DATE` | From first date to second (exclusive end) |
| `DATE..` | From date onward (open end) |
| `..DATE` | Up to date (exclusive, open start) |
| `from DATE` / `since DATE` | Same as `DATE..` |
| `to DATE` / `until DATE` | Same as `..DATE` |
| `YYYY` | Whole year span |
| `YYYY-MM` | Whole month span |
| `YYYYqN` / `YYYYQN` | Whole quarter (e.g., `2024q1`) |
| `in DATE` | The containing period |

## Report Periods

Control the date range of reports.

| Option | Description |
|--------|-------------|
| `-b DATE` / `--begin DATE` | Report start date (inclusive) |
| `-e DATE` / `--end DATE` | Report end date (exclusive) |
| `-p PERIODEXPR` / `--period PERIODEXPR` | Combined interval + span |

When multiple period options conflict, the **rightmost wins**.

Period expression examples:
```
-p "monthly from 2024-01 to 2024-07"
-p "weekly in 2024"
-p "quarterly this year"
```

## Report Intervals

Intervals subdivide a report period into sub-periods.

### Basic Intervals

| Interval | Alternatives |
|----------|-------------|
| `daily` | `every day` |
| `weekly` | `every week` |
| `monthly` | `every month` |
| `quarterly` | `every quarter` |
| `yearly` | `every year` |
| `biweekly` | `fortnightly` |
| `bimonthly` | — |

### Every-N Intervals

```
every N days
every N weeks
every N months
every N quarters
every N years
```

### Advanced Intervals

```
every Nth day of week          # e.g., every 2nd day of week
every Nth day [of month]       # e.g., every 15th day
every Nth WEEKDAY [of month]   # e.g., every 2nd friday
every MONTH Nth [of year]      # e.g., every march 1st
every weekday
every weekendday
every monday,wednesday,friday
```

## CLI Interval Flags

Shorthand flags for common intervals:

| Flag | Interval |
|------|----------|
| `-D` | Daily |
| `-W` | Weekly |
| `-M` | Monthly |
| `-Q` | Quarterly |
| `-Y` | Yearly |

These are equivalent to using `--period` with the corresponding interval word.
