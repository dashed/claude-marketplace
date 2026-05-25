# hledger Journal Format Reference

Complete reference for hledger's journal file format (`.journal`, `.j`, `.hledger`, `.ledger`).

## Transaction Syntax

```
DATE[=DATE2] [STATUS] [(CODE)] DESCRIPTION [; COMMENT]
    [STATUS] ACCOUNT  [AMOUNT] [COST] [BALANCE ASSERTION] [; COMMENT]
    [STATUS] ACCOUNT  [AMOUNT] [COST] [BALANCE ASSERTION] [; COMMENT]
```

- **Date**: `YYYY-MM-DD`, `YYYY.MM.DD`, or `YYYY/MM/DD`
- **Secondary date**: `=DATE` after primary (e.g., `2024-01-15=2024-01-16`)
- **Datetime**: `DATE HH:MM[:SS][+-ZZZZ]`
- **Status**: ` ` (unmarked), `!` (pending), `*` (cleared)
- **Code**: `(REF)` — free text in parentheses
- **Description**: free text until `;` or newline

```journal
2024-01-15=2024-01-16 * (INV-042) Office supplies ; project:ops
    expenses:office           $50.00
    assets:checking
```

## Posting Syntax

```
  [STATUS] ACCOUNTNAME  [AMOUNT] [COST] [BALANCEASSERTION] [; COMMENT]
```

- Must start with at least one space or tab
- Account name: colon-separated parts (e.g., `assets:bank:checking`)
- Account terminated by **double space**, tab, or end of line
- At most one posting may omit the amount (inferred)

## Amount Syntax

```
[SIGN] [COMMODITY] QUANTITY [COMMODITY]
```

| Feature | Examples |
|---------|----------|
| Left commodity | `$100`, `£50.00` |
| Right commodity | `100 EUR`, `50.00 CAD` |
| Negative | `-$100`, `$-100` |
| Decimal mark | `.` or `,` (`$1,000.00` or `€1.000,00`) |
| Digit groups | `,` or `.` or Unicode spaces (`1,000` or `1.000` or `1 000`) |
| Exponents | `1.5e3`, `2E-4` |
| Quoted commodity | `"AAPL"`, `"BRK.B"` |

Simple commodity symbols: anything except digits, spaces, and special characters (`-+.@*;\t\n"{}=`).

## Cost Notation

| Syntax | Meaning | Example |
|--------|---------|---------|
| `@ PRICE` | Unit cost | `10 AAPL @ $150` |
| `@@ PRICE` | Total cost | `10 AAPL @@ $1500` |
| `(@) PRICE` | Unit cost (parenthesized) | `10 AAPL (@) $150` |
| `(@@) PRICE` | Total cost (parenthesized) | `10 AAPL (@@) $1500` |

## Balance Assertions

| Syntax | Scope | Description |
|--------|-------|-------------|
| `= AMOUNT` | Single commodity, this account | Assert balance of one commodity |
| `== AMOUNT` | All commodities, this account | Assert total balance (multi-commodity) |
| `=* AMOUNT` | Single commodity, inclusive of subaccounts | Assert including subaccounts |
| `==* AMOUNT` | All commodities, inclusive of subaccounts | Assert total including subaccounts |

```journal
2024-01-15 Paycheck
    assets:checking       $5000 = $12000
    income:salary
```

## Directives

### Account Declaration

```journal
account expenses:food
    ; type:X
    ; A comment about this account
```

### Commodity Declaration

One-line form:

```journal
commodity $1,000.00
```

Multi-line form:

```journal
commodity $
    format $1,000.00
```

### Complete Directive Reference

| Directive | Syntax | Purpose |
|-----------|--------|---------|
| `account` | `account ACCTNAME [; comment]` | Declare account, set type/comments |
| `commodity` | `commodity AMOUNT` or multi-line with `format` | Declare display style |
| `payee` | `payee NAME [; comment]` | Declare payee |
| `tag` | `tag NAME [; comment]` | Declare tag |
| `P` | `P DATE COMMODITY AMOUNT` | Market price |
| `D` | `D AMOUNT` | Default commodity |
| `include` | `include PATHORGLOB` | Include files |
| `alias` | `alias OLD = NEW` or `alias /REGEX/ = REPL` | Account alias |
| `end aliases` | `end aliases` | Clear all aliases |
| `comment` / `end comment` | Block delimiters | Multi-line comment |
| `Y` or `year` | `Y YEAR` | Default year (>=4 digits) |
| `decimal-mark` | `decimal-mark .` or `decimal-mark ,` | Set decimal character |
| `apply account` | `apply account ACCTNAME` | Prefix all accounts |
| `end apply account` | `end apply account` | Stop prefixing |
| `=` | `= QUERY` + postings | Transaction modifier (auto postings) |
| `~` | `~ PERIODEXPR` + postings | Periodic transaction (budget/forecast) |
| `N` | `N COMMODITY` | Ignored-price commodity (parsed, not used) |
| `C` | `C AMT1 = AMT2` | Commodity conversion (parsed, not used) |

Ledger-compatible directives (parsed, ignored): `apply fixed`, `end apply fixed`, `apply tag`, `end apply tag`, `end apply year`, `end tag`, `assert`, `bucket`/`A`, `capture`, `check`, `define`, `expr`, `value`, `eval`, `python`.

## Account Types

| Code | Type | Auto-inferred from |
|------|------|--------------------|
| `A` | Asset | `assets` |
| `L` | Liability | `liabilities`, `debts` |
| `E` | Equity | `equity` |
| `R` | Revenue | `income`, `revenue` |
| `X` | Expense | `expenses` |
| `C` | Cash | `assets:cash`, `assets:bank`, `assets:checking`, `assets:savings`, `assets:current` |
| `V` | Conversion | `equity:trade`, `equity:trading`, `equity:conversion` |

Set explicitly with the `type:` tag in account declarations:

```journal
account assets:crypto
    ; type:A
```

## Tags

Tags are `name:value` pairs in comments.

```journal
2024-01-15 Lunch ; trip:paris, meal:lunch
    expenses:food          $25.00 ; vendor:cafe
    assets:cash
```

| Feature | Syntax | Notes |
|---------|--------|-------|
| Inline tag | `; name:value` | Value extends to comma or newline |
| Multiple tags | `; tag1:val1, tag2:val2` | Comma-separated |
| Valueless tag | `; name:` | Empty value |
| Hidden tag | `; _internal:val` | Names starting with `_` |
| Date tag | `; date:2024-02-01` | Overrides posting date |
| Date2 tag | `; date2:2024-02-01` | Overrides secondary date |
| Bracketed date | `; [2024-02-01]` | Shorthand for date tag |
| Bracketed both | `; [2024-02-01=2024-02-02]` | Sets date and date2 |

The tag name is the last word before the colon.

## Virtual Postings

| Syntax | Type | Balanced? |
|--------|------|-----------|
| `account` | Real | Yes (required) |
| `(account)` | Virtual (unbalanced) | No |
| `[account]` | Balanced virtual | Yes (required) |

```journal
2024-01-15 Paycheck
    assets:checking           $5000
    income:salary            -$5000
    (budget:available)        $5000   ; unbalanced virtual
    [assets:checking]         $1000   ; balanced virtual
    [assets:savings]         -$1000
```

## Date Formats

| Format | Example |
|--------|---------|
| ISO | `2024-01-15` |
| Dotted | `2024.01.15` |
| Slashed | `2024/01/15` |
| With secondary | `2024-01-15=2024-01-16` |
| Datetime | `2024-01-15 14:30:00` |
| Datetime + TZ | `2024-01-15 14:30:00+0530` |

Separators must be consistent within a single date. Partial dates are allowed when a `Y` directive sets the default year.

## Transaction Modifier Rules

Auto-posting rules that add postings to matching transactions. Enabled with `--auto`.

```journal
= expenses:food
    budget:food              *-1    ; multiply matched posting amount by -1

= desc:grocery
    liabilities:tax           0.10  ; flat amount
```

- `*` prefix multiplies the matched posting's amount
- Adds `_generated-posting` tag to generated postings
- Query matches against the original transaction

## Periodic Transaction Rules

Define recurring transactions for `--forecast` and `--budget`.

```journal
~ monthly from 2024-01  * Rent
    expenses:rent            $2000
    assets:checking

~ every 2 weeks  Paycheck
    assets:checking          $5000
    income:salary
```

- Period expression: `monthly`, `weekly`, `every N days/weeks/months`, `every 1st of month`, etc.
- Adds `recur:PERIODEXPR` and `generated-transaction` tags
- Used with `--forecast` to generate future transactions
- Used with `--budget` for budget reports

## Comment Syntax

| Type | Syntax | Context |
|------|--------|---------|
| Line comment | `; text` | Start of line |
| Line comment | `# text` | Start of line |
| Line comment | `* text` | Start of line |
| Inline comment | `; text` | After transaction/posting data |
| Block comment | `comment` ... `end comment` | Multi-line block |

Only `;` works for inline (same-line) comments. `#` and `*` work only at the start of a line.

## Include Directive

```journal
include expenses.journal
include accounts/*.journal
include ~/finance/**/*.journal
include csv:bank-export.csv
```

| Feature | Example |
|---------|---------|
| Simple glob | `include *.journal` |
| Recursive glob | `include **/*.journal` |
| Home directory | `include ~/finance/main.journal` |
| Reader prefix | `include csv:data.csv` |
| Reader prefixes | `csv:`, `tsv:`, `ssv:`, `journal:`, `timeclock:`, `timedot:` |

Paths are relative to the including file. Circular includes are detected.

## Account Aliases

```journal
alias savings = assets:bank:savings
alias /^expenses:misc(.*)/ = expenses:other\1
```

| Type | Syntax | Behavior |
|------|--------|----------|
| Plain | `alias OLD = NEW` | Prefix replacement |
| Regex | `alias /REGEX/ = REPLACEMENT` | Case-insensitive regex substitution |
| Clear | `end aliases` | Remove all active aliases |

Aliases are applied in the order they are defined.

## Timeclock Format

File extension: `.timeclock`. Clock in/out tracking.

```timeclock
i 2024-01-15 09:00:00 work:project-a  Started feature work
o 2024-01-15 12:30:00
i 2024-01-15 13:00:00 work:project-a  After lunch
o 2024-01-15 17:00:00
```

- `i DATETIME ACCOUNT [DESCRIPTION]` — clock in
- `o DATETIME` — clock out
- Sessions spanning midnight are automatically split
- Amounts are recorded in hours

## Timedot Format

File extension: `.timedot`. Simple time logging.

```timedot
2024-01-15
work:project-a   .... .... ..   ; 2.5h (each dot = 0.25h)
work:project-b   3h
admin:email      30m
```

| Duration syntax | Meaning |
|-----------------|---------|
| `.` (dot) | 0.25 hours each |
| `8h` | 8 hours |
| `30m` | 30 minutes |
| `5s` | 5 seconds |
| `1d` | 1 day |
| `1w` | 1 week |
| `1mo` | 1 month |
| `1y` | 1 year |
| Letters (e.g., `aaaa`) | 0.25h each, with `t:TAG` support |

## Supported File Formats

| Extension | Format | Reader prefix |
|-----------|--------|---------------|
| `.journal`, `.j`, `.hledger`, `.ledger` | Journal | `journal:` |
| `.timeclock` | Timeclock | `timeclock:` |
| `.timedot` | Timedot | `timedot:` |
| `.csv` | CSV | `csv:` |
| `.tsv` | TSV | `tsv:` |
| `.ssv` | SSV (semicolon-separated) | `ssv:` |
