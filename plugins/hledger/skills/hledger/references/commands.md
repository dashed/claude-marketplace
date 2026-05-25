# hledger Command Reference

## Global Flags

### Input

| Flag | Description |
|------|-------------|
| `-f, --file [FMT:]FILE` | Journal file (- = stdin, multiple allowed, format from extension or prefix) |
| `--rules RULESFILE` | CSV/TSV rules file |
| `--alias A=B\|/RGX/=RPL` | Account name alias (literal or regex) |
| `--auto` | Enable auto posting rules (`=` directives) |
| `--forecast[=PERIOD]` | Enable periodic transaction rules (`~` directives) |
| `-I, --ignore-assertions` | Skip balance assertions |
| `--infer-costs` | Infer conversion equity postings from costs |
| `--infer-equity` | Infer costs from conversion equity postings |
| `--infer-market-prices` | Infer market prices from costs |
| `--pivot TAGNAME` | Use tag value as account name |
| `-s, --strict` | Extra error checks (accounts/commodities must be declared) |
| `--verbose-tags` | Add generated/modified tags to output |

### Period

| Flag | Description |
|------|-------------|
| `-b, --begin DATE` | Start date (inclusive) |
| `-e, --end DATE` | End date (exclusive) |
| `-p, --period PERIODEXP` | Flexible period expression (combines begin/end/interval) |
| `-D` | Daily intervals |
| `-W` | Weekly intervals |
| `-M` | Monthly intervals |
| `-Q` | Quarterly intervals |
| `-Y` | Yearly intervals |
| `--today DATE` | Override today's date |
| `--date2` | Use secondary dates |

### Status & Filter

| Flag | Description |
|------|-------------|
| `-U, --unmarked` | Show only unmarked transactions |
| `-P, --pending` | Show only pending (!) transactions |
| `-C, --cleared` | Show only cleared (*) transactions |
| `-R, --real` | Non-virtual postings only |
| `-E, --empty` | Show zero-balance items |
| `--depth DEPTHEXP` | Limit account depth |

### Valuation

| Flag | Description |
|------|-------------|
| `-B, --cost` | Convert to cost basis |
| `-V, --market` | Market value at period end |
| `-X, --exchange COMM` | Market value in specific commodity |
| `--value WHEN[,COMM]` | Custom valuation (then/end/now/YYYY-MM-DD) |

### Display

| Flag | Description |
|------|-------------|
| `-c, --commodity-style S` | Override commodity display style |
| `--pretty[=YN]` | Use box-drawing characters |
| `--color YNA` | ANSI color (yes/no/auto) |
| `--pager YN` | Use pager for output |
| `-O, --output-format FMT` | txt, csv, tsv, json, html, fods, sql, beancount |
| `-o, --output-file FILE` | Write output to file |

### Config

| Flag | Description |
|------|-------------|
| `--conf CONFFILE` | Use specific config file |
| `-n, --no-conf` | Ignore config files |
| `--debug[=1-9]` | Debug level |

---

## Help Commands

| Command | Description |
|---------|-------------|
| `hledger` | Show command list |
| `hledger help [TOPIC]` | Show manual or topic |
| `hledger demo [-s SPEED]` | Play terminal demos |
| `hledger setup` | Check installation status (experimental) |

---

## Data Entry

### add

Interactive transaction entry with tab completion for accounts and descriptions.

| Flag | Description |
|------|-------------|
| `--no-new-accounts` | Only allow existing accounts |

### import

Import transactions with automatic duplicate detection using `.latest` files.

| Flag | Description |
|------|-------------|
| `--catchup` | Mark file as imported without adding transactions |
| `--dry-run` | Show what would be imported |

---

## List Commands

| Command | Description | Key Flags |
|---------|-------------|-----------|
| `accounts` | List account names | `--used`, `--declared`, `--undeclared`, `--unused`, `--find`, `--directives`, `--locations`, `--types`, `-l/--flat`, `-t/--tree`, `--drop=N` |
| `codes` | List transaction codes | — |
| `commodities` | List commodity symbols | `--used`, `--declared`, `--undeclared`, `--unused`, `--find` |
| `descriptions` | List unique descriptions (alphabetical) | — |
| `files` | List included journal files | Args: `[REGEX]` |
| `notes` | List unique notes (after `\|` in description) | — |
| `payees` | List unique payees (before `\|` in description) | `--used`, `--declared`, `--undeclared`, `--unused`, `--find` |
| `prices` | List market prices (P directive format) | `--show-reverse` |
| `tags` | List tag names/values | `--used`, `--declared`, `--undeclared`, `--unused`, `--find`, `--values`, `--parsed` |
| `stats` | Journal statistics | `-1` (single line), `-v/--verbose` |

All list commands output text only.

---

## Standard Reports

### print

Show full journal entries as they were recorded.

| Flag | Description |
|------|-------------|
| `-x, --explicit` | Show all amounts explicitly |
| `--invert` | Negate amounts |
| `--locations` | Show file/line locations |
| `-m, --match=DESC` | Find best match for description |
| `--new` | Show only new transactions (since last run) |
| `--round=TYPE` | Rounding type |

**Formats:** txt, beancount, csv, tsv, html, fods, json, sql

### register (reg)

Show postings with running total.

| Flag | Description |
|------|-------------|
| `--cumulative` | Running total (default) |
| `-H, --historical` | Running total including prior periods |
| `-A, --average` | Running average |
| `-m, --match` | Fuzzy match description |
| `-r, --related` | Show other postings in matched transactions |
| `--invert` | Negate amounts |
| `--sort=FIELDS` | Sort by fields |
| `-w, --width` | Output width |
| `--align-all` | Align all columns |

**Formats:** txt, csv, tsv, html, fods, json

### aregister (areg)

Account register in bank-statement style. Args: `ACCTPAT [QUERY]`

| Flag | Description |
|------|-------------|
| `--txn-dates` | Show transaction dates |
| `--no-elide` | Don't abbreviate |
| `-H, --historical` | Include prior balance (default) |
| `--invert` | Negate amounts |
| `-w, --width` | Output width |
| `--align-all` | Align all columns |

**Formats:** txt, html, csv, tsv, json

### balance (bal)

The most flexible report command.

**Calculation modes:**

| Flag | Description |
|------|-------------|
| `--sum` | Sum of amounts (default) |
| `--valuechange` | Change in market value |
| `--gain` | Unrealised capital gain/loss |
| `--budget[=DESCPAT]` | Budget report |
| `--count` | Count of postings |

**Accumulation:**

| Flag | Description |
|------|-------------|
| `--change` | Change in period |
| `--cumulative` | Cumulative from report start |
| `-H, --historical` | Historical ending balance |

**Layout:**

| Flag | Description |
|------|-------------|
| `--layout=wide[,W]` | Wide multi-column |
| `--layout=tall` | One row per amount |
| `--layout=bare` | Minimal |
| `--layout=tidy` | Tidy data format |

**Other:** `-r/--related`, `--invert`, `--transpose`, `-l/--flat`, `-t/--tree`, `--drop=N`, `-A/--average`, `-T/--row-total`, `--summary-only`, `-N/--no-total`, `--no-elide`, `--format=FMTSTR`, `-S/--sort-amount`, `-%/--percent`, `--base-url`

**Formats:** txt, html, csv, tsv, json, fods

### Compound Balance Reports

| Command | Alias | Shows | Default Mode |
|---------|-------|-------|--------------|
| `balancesheet` | `bs` | Assets + Liabilities | `-H` (historical) |
| `balancesheetequity` | `bse` | Assets + Liabilities + Equity | `-H` (historical) |
| `incomestatement` | `is` | Revenue + Expenses | `--change` |
| `cashflow` | `cf` | Liquid asset changes | `--change` |

All support: `--sum/--valuechange/--gain/--count`, `--change/--cumulative/-H`, `-l/--flat/-t/--tree`, `--drop=N`, `--declared`, `-A/--average`, `-T/--row-total`, `--summary-only`, `-N/--no-total`, `--no-elide`, `--format=FMTSTR`, `-S/--sort-amount`, `-%/--percent`, `--layout=ARG`, `--base-url`

**Formats:** txt, html, csv, tsv, json

---

## Advanced Commands

### roi

Calculate Internal Rate of Return (IRR) and Time-Weighted Return (TWR).

| Flag | Description |
|------|-------------|
| `--investment=QUERY` | Query for investment accounts |
| `--profit-loss=QUERY` | Query for P&L accounts (alias: `--pnl`) |
| `--cashflow` | Show cash flows used in calculation |

Text output only.

### activity

Show bar chart of posting counts per period. Text output only.

### close (equity)

Generate closing/opening transactions for period transitions.

| Mode | Description |
|------|-------------|
| `--clopen` | Generate both closing and opening entries |
| `--close` | Closing entries only (default) |
| `--open` | Opening entries only |
| `--assert` | Balance assertions |
| `--assign` | Balance assignments |
| `--retain` | Retain earnings entry |

| Flag | Description |
|------|-------------|
| `-x, --explicit` | Show all amounts |
| `--show-costs` | Show costs in output |
| `--interleaved` | Interleave close/open |
| `--assertion-type=TYPE` | Assertion type |
| `--close-desc/--close-acct` | Customize closing entry |
| `--open-desc/--open-acct` | Customize opening entry |
| `--round=TYPE` | Rounding type |

Adds tags: `clopen:`, `assert:`, `assign:`, `retain:`

### rewrite

Print journal with automatically added postings.

| Flag | Description |
|------|-------------|
| `--add-posting='ACCT  AMTEXPR'` | Add posting (AMTEXPR: literal or *N multiplier) |
| `--diff` | Show unified diff output |

### check

Run correctness checks on journal data.

**Basic checks** (always run): parseable, autobalanced, assertions

**Strict checks** (`-s`): balanced, commodities, accounts

**Optional checks:** ordereddates, payees, tags, recentassertions, uniqueleafnames

Check names are prefix-matchable (e.g., `ord` matches `ordereddates`).

### diff

Compare transactions between two files.

```
hledger diff -f FILE1 -f FILE2 ACCTNAME
```

### run / repl

Run multiple commands with data parsed only once.

```
hledger run -- CMD1 -- CMD2
```

Or provide a script file with one command per line.

---

## Command Aliases

| Full Name | Alias |
|-----------|-------|
| `balance` | `bal` |
| `balancesheet` | `bs` |
| `balancesheetequity` | `bse` |
| `cashflow` | `cf` |
| `incomestatement` | `is` |
| `register` | `reg` |
| `aregister` | `areg` |
| `close` | `equity` |

---

## Notable Addon Commands

| Addon | Description |
|-------|-------------|
| `hledger-ui` | Terminal UI (curses) |
| `hledger-web` | Web interface |
| `hledger-iadd` | Interactive add (improved) |
| `hledger-edit` | Open matching entries in editor |
| `hledger-lots` | Track lots/cost basis |
| `hledger-bar` | Bar chart reports |
| `hledger-plot` | Plotting reports |
| `hledger-autosync` | Sync with OFX/bank feeds |
| `hledger-interest` | Interest calculation |
| `hledger-pricehist` | Fetch historical prices |
| `hledger-git` / `hledger-pijul` | VCS integration |
| `hledger-check-fancyassertions` | Advanced balance assertions |
| `hledger-check-tagfiles` | Validate tag values as file paths |

Addons are any `hledger-*` executables on PATH. Run with `hledger ADDON` (drop the prefix).
