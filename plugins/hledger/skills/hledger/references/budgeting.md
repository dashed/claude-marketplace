# Budgeting, Time Tracking & Advanced Features

## Budgeting with Periodic Transactions

Define budget goals using `~` periodic transaction rules:

```journal
~ monthly
    (expenses:food)         $500
    (expenses:transport)    $200
    (expenses:housing)      $1500

~ weekly
    (expenses:dining)       $75

~ quarterly
    (expenses:insurance)    $600
```

Periodic transactions define expected amounts per period. They don't generate actual transactions — they set targets for budget reports.

## Budget Reports

Use `--budget` with balance commands to compare actuals against goals:

```bash
hledger bal --budget -M expenses
hledger bal --budget -Q expenses:food
hledger bal --budget --budget=food -M    # filter by periodic rule description
```

Output format shows actual spending vs. budget goal:

```
                 Jan            Feb            Mar
expenses:food    $420 [84% of $500]   $530 [106% of $500]   $480 [96% of $500]
```

Useful flags:

| Flag | Effect |
|------|--------|
| `--budget` | Compare actuals to all periodic rules |
| `--budget=DESCPAT` | Filter which periodic rules apply |
| `-E` | Show unbudgeted accounts (those without matching rules) |
| `-M` / `-Q` / `-Y` | Monthly / quarterly / yearly columns |

## Forecasting

The `--forecast` flag generates future transactions from `~` periodic rules:

```bash
hledger reg --forecast expenses:food
hledger bal --forecast -M expenses
hledger reg --forecast=2026-06..2026-12 expenses
```

Generated transactions receive automatic tags:
- `recur:PERIODEXPR` — the period expression that generated it
- `generated-transaction:~PERIODEXPR` — full source reference

Use forecasting to project cash flow or see upcoming expected expenses.

## Time Tracking — Timedot Format

Files with `.timedot` extension use a simple duration-per-line format:

```timedot
2026-05-25
projects:clientA    .... ..    ; 1.5h (each dot = 0.25h, spaces ignored)
projects:clientB    3.5h       ; numeric with unit
admin:email         2          ; plain number = hours

2026-05-26
projects:clientA    ......     ; 1.5h
learning:haskell    45m        ; 45 minutes
```

Duration formats:
- **Dots**: each `.` = 0.25h, spaces between dots ignored
- **Numbers**: optional unit suffix — `s`, `m`, `h`, `d`, `w`, `mo`, `y`
- **Letters**: each letter = 0.25h, generates `t:LETTER` tag

Notes:
- Org-mode heading prefixes (`*`) allowed for account names
- All transactions marked as cleared (`*`)
- All postings are virtual (parenthesized)

## Time Tracking — Timeclock Format

Files with `.timeclock` extension use clock-in/clock-out pairs:

```timeclock
i 2026-05-25 09:00:00 projects:clientA  started feature work
o 2026-05-25 12:30:00
i 2026-05-25 13:00:00 projects:clientB  code review
o 2026-05-25 15:00:00
i 2026-05-25 15:15:00 admin:meetings
o 2026-05-25 16:00:00
```

Format:
- `i DATETIME ACCOUNT [DESCRIPTION]` — clock in
- `o DATETIME [ACCOUNT]` — clock out

Behavior:
- Sessions spanning midnight are automatically split
- Multiple concurrent sessions supported (matched by account name)
- Amounts recorded in hours
- All postings are virtual

## Time Reporting Examples

```bash
# Total hours by project this week
hledger -f time.timedot bal -W

# Daily breakdown
hledger -f time.timedot reg -D projects

# Hours per client this month
hledger -f time.timedot bal -M projects

# Combine with journal for billing
hledger bal -f time.timedot -f rates.journal --pivot client
```

## ROI Command

Calculate Internal Rate of Return (IRR) and Time-Weighted Return (TWR) for investments:

```bash
hledger roi --inv assets:broker --pnl income:capital-gains -Y
hledger roi --inv assets:stocks --pnl income:dividends -Q --cashflow
hledger roi --inv assets:crypto --pnl income:crypto -M
```

Required flags:
- `--investment=QUERY` / `--inv` — accounts holding investments
- `--profit-loss=QUERY` / `--pnl` — accounts recording gains/losses

Optional flags:
- `--cashflow` — show cash flow amounts in output
- `-M` / `-Q` / `-Y` — reporting period

Output columns:

| Column | Meaning |
|--------|---------|
| Begin / End | Period boundaries |
| Value begin / end | Portfolio value at start/end |
| Cashflow | Net cash in/out |
| PnL | Profit or loss |
| IRR% | Money-weighted return (annualized, Newton's method) |
| TWR/period% | Time-weighted return for period |
| TWR/year% | Time-weighted return annualized |

## Year-End Closing (close command)

The `close` command has 6 modes for different year-end operations:

| Mode | Purpose | Default accounts |
|------|---------|-----------------|
| `--clopen` | Closing + opening pair for file migration | Assets+Liabilities → equity:opening/closing balances |
| `--close` | Just the closing transaction (default) | Assets+Liabilities → equity:closing balances |
| `--open` | Just the opening transaction | equity:opening balances → Assets+Liabilities |
| `--assert` | Balance assertion transaction | Asserts current balances |
| `--assign` | Balance assignment transaction | Assigns current balances |
| `--retain` | Retain earnings | Revenue+Expense → equity:retained earnings |

```bash
# Generate closing + opening for new year file
hledger close --clopen -e 2027 >> 2026.journal

# Retain earnings at year end
hledger close --retain -e 2027 >> 2026.journal

# Generate balance assertions for verification
hledger close --assert -e 2027 >> 2027.journal
```

Key flags:

| Flag | Effect |
|------|--------|
| `-x` / `--explicit` | Show all amounts explicitly |
| `--show-costs` | Include cost information |
| `--interleaved` | Interleave closing/opening postings |
| `--assertion-type` | `=`, `==`, `=*`, `==*` |
| `--close-desc` / `--close-acct` | Customize closing transaction |
| `--open-desc` / `--open-acct` | Customize opening transaction |
| `--round=TYPE` | Rounding method for amounts |

Auto-generated tags: `clopen:`, `assert:`, `assign:`, `retain:` with auto-incremented year.

Date behavior: closing date = yesterday or journal end date; opening date = closing + 1 day.

## Configuration File

hledger reads options from `hledger.conf`:

```conf
# General options (outside any section)
--strict
-f ~/finance/2026.journal
-f ~/finance/2025.journal

# Command-specific options
[balance]
--tree
-M

[register]
--width=120

[bal]
--layout=bare
```

Search order (first found wins):
1. `./hledger.conf` (current directory)
2. Parent directories (walking up)
3. `~/.hledger.conf`
4. `~/.config/hledger/hledger.conf`

Override: `--conf=FILE` to specify, `--no-conf` / `-n` to skip.

Comments use `#`.

## hledger-web

Web interface for browsing and editing journals:

```bash
hledger-web                          # default: serve, open browser, auto-exit
hledger-web --serve                  # serve without auto-exit
hledger-web --serve-api              # JSON API only
hledger-web --host=0.0.0.0 --port=8080  # network accessible
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | 127.0.0.1 | Listen address |
| `--port` | 5000 | Listen port |
| `--socket` | — | Unix socket path |
| `--base-url` | — | URL prefix for reverse proxy |
| `--allow` | view | Permission level: view/add/edit/sandstorm |
| `--cors` | — | CORS origin header |

Features: accounts sidebar, register views, charts, data entry form, JSON API, automatic backup on edit.

## hledger-ui

Terminal interface with interactive navigation:

```bash
hledger-ui                           # default accounts screen
hledger-ui --watch                   # auto-reload on file changes
hledger-ui --theme=dark              # dark theme
hledger-ui --bs                      # start on balance sheet
hledger-ui --register=expenses:food  # jump to register
```

Startup options:

| Option | Effect |
|--------|--------|
| `-w` / `--watch` | Auto-reload on file changes |
| `--theme` | default / greenterm / terminal / dark |
| `--cash` / `--bs` / `--is` / `--all` | Starting screen |
| `--register=ACCT` | Open specific account register |
| `--change` | Show changes instead of balances |
| `-l` / `--flat` | Flat account list |
| `-t` / `--tree` | Tree account list |

Navigation keys:

| Key | Action |
|-----|--------|
| `?` | Help |
| `RIGHT` / `ENTER` | Drill deeper |
| `LEFT` / `ESC` | Go back |
| `/` | Filter accounts |
| `F` | Toggle forecast |
| `SHIFT+←/→` | Change period |
| `g` | Reload data |
| `a` | Add transaction |
| `E` | Open in editor |
| `B` | Toggle cost basis |
| `V` | Toggle market value |
| `H` | Toggle historical |
| `U` / `P` / `C` | Filter by status (unmarked/pending/cleared) |
| `R` | Toggle real (non-virtual) |
| `z` | Toggle nonzero |
| `q` | Quit |

Screens: Menu → Cash / BS / IS / All accounts → Register → Transaction detail.
