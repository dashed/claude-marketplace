---
name: gogcli
description: Drive Google Workspace from the terminal with the `gog` CLI (gogcli). Use when sending or searching Gmail, managing labels/drafts/filters, creating or updating Google Calendar events (including recurring, focus-time, or out-of-office), uploading/downloading/sharing Google Drive files, reading or writing Google Sheets, editing or exporting Google Docs and Slides, managing Google Contacts or the Workspace directory, working with Google Tasks (including recurrence), posting to Google Chat spaces, running Apps Script functions, creating Forms, administering Workspace users/groups via a DWD service account, or when building agent workflows that need multi-account Google access with JSON output, OAuth/ADC/service-account auth, Pub/Sub watches, email-open tracking, or an `--enable-commands` sandbox. Invoke any time the user mentions gogcli, the `gog` command, a Google CLI, or a one-stop terminal tool for Gmail/Calendar/Drive/Docs/Sheets/Slides/Chat/Tasks/Contacts/Classroom/Forms/Keep/Admin.
---

# gogcli — Google Workspace in the terminal

`gogcli` (binary name: `gog`) is a single Go CLI that covers Gmail, Calendar, Drive, Docs, Slides, Sheets, Chat, Tasks, Contacts, People, Classroom, Forms, Apps Script, Keep, Admin (Directory), and Cloud Identity Groups. It is JSON-first, multi-account, and designed for agents as well as humans.

**Binary:** `gog` (not `gogcli`). **Repo:** `github.com/steipete/gogcli`. **Latest release at time of writing:** 0.12.0.

---

## When to Use

Trigger this skill whenever the user asks to do any of the following from the terminal or a script/agent:

- Send, draft, or reply to a Gmail message; search Gmail with operators (`from:`, `newer_than:7d`, `is:unread`); manage labels, filters, vacation responder, send-as, delegates, or forwarding.
- Create/list/update/delete Google Calendar events, including recurring events (RRULE), focus-time, out-of-office, working-location, and free/busy lookups.
- List, search, upload, download, replace, move, share, or permission-manage Google Drive files and folders, including shared drives and Workspace file conversions.
- Read/write/append/clear Google Sheets ranges, insert rows/columns, manage tabs and named ranges, apply formatting/merge/freeze/number-format, or run find/replace.
- Create, edit, find/replace, sed-regex-edit, or export Google Docs; generate Slides decks from Markdown or templates; export Docs/Slides as PDF/DOCX/PPTX/Markdown.
- Manage Google Contacts (CRUD with custom fields), query the Workspace directory, or manage Google Tasks with client-materialized recurrence.
- Post messages to Google Chat spaces/DMs/threads; manage reactions.
- Administer a Google Workspace domain (users, groups, members) via a domain-wide-delegation service account.
- Authenticate one or more Google accounts for CLI/CI/headless use via OAuth, Application Default Credentials, a direct access token, or a service account.
- Build agent workflows that need stable JSON output, deterministic exit codes, a machine-readable schema of the CLI, or a command allowlist sandbox.
- Operate Pub/Sub push handlers for Gmail or Forms; set up email-open tracking via a Cloudflare Worker.

---

## Prerequisites

### Install the `gog` binary

```bash
# macOS / Linux (Homebrew Core)
brew install gogcli

# Arch Linux (AUR)
yay -S gogcli

# From source (Go 1.25+)
git clone https://github.com/steipete/gogcli.git
cd gogcli
make            # outputs ./bin/gog
```

### Verify

```bash
command -v gog && gog --version
```

### Google Cloud project

Each service group calls a different API. Enable the APIs you need on the Google Cloud project that owns your OAuth client (or service account):

- Gmail, Calendar, Drive, Docs, Slides, Sheets, People, Tasks API for the user-facing groups.
- Chat API for `chat` (Workspace only).
- Admin SDK + Cloud Identity API for `admin` and `groups` (DWD service account).
- Classroom, Forms, Apps Script, Keep APIs for the respective groups.

The upstream README lists the enable URLs for each. `gog auth services` prints the full scope list needed when registering DWD.

---

## First-time setup (OAuth, single account)

```bash
# 1. Store a Desktop OAuth client JSON once.
gog auth credentials /path/to/client_secret.json

# 2. Launch browser OAuth and persist a refresh token in the OS keyring.
gog auth add you@example.com

# 3. Verify status and stored accounts.
gog auth status
gog auth list --check
```

For headless/CI, ADC, service-account (DWD), `--manual`, `--remote`, `--access-token`, custom redirect URIs, least-privilege scope flags (`--services`, `--readonly`, `--drive-scope`, `--gmail-scope`, `--extra-scopes`), multiple OAuth clients, and keyring backends (`keychain` / `file` / `auto`), see **[references/auth.md](references/auth.md)**.

---

## Agent-mode essentials

### Output modes

| Flag / Env | Effect |
|---|---|
| `--json` (alias `--machine`, `-j`) | Emit JSON on stdout. |
| `--plain` (alias `--tsv`, `-p`) | Stable TSV on stdout; disables colors. |
| `GOG_AUTO_JSON=1` | Auto-switch to JSON when stdout is not a TTY. Opt-in agent mode. |
| `GOG_JSON=1` / `GOG_PLAIN=1` | Force mode (overridden by explicit flags). |
| `--select`/`--fields`/`--pick`/`--project <a,b,c>` | Project only these dot-paths from JSON output. |
| `--results-only` | Strip envelope (`nextPageToken`, etc.); emit only the primary result. |
| `NO_COLOR=1` | Disable ANSI colors. |

**Gotcha:** `--fields` is silently rewritten to `--select` everywhere **except** `calendar events|ls|list`, where `fields` is the Calendar API selector. Use `--select` to be unambiguous.

### Safety rails

| Flag | Effect |
|---|---|
| `--dry-run` (aliases `-n`, `--noop`, `--preview`, `--dryrun`) | Print intended actions, succeed. Honored by destructive commands (`gmail archive|read|unread|trash`, `drive delete`, `sheets delete-tab`, `forms delete-question`, etc.). |
| `--force` (aliases `-y`, `--yes`, `--assume-yes`) | Skip confirmations. |
| `--no-input` / `--non-interactive` | Never prompt; fail instead. Public Drive shares, Gmail forwarding filters, and delegate grants still require `--force`. |
| `--verbose` | Extra diagnostic output on stderr. |

### Schema + exit codes for agents

```bash
gog schema                  # Full CLI JSON schema (aliases: help-json, helpjson).
gog schema calendar create  # Scope to a sub-tree.
gog agent exit-codes        # Stable exit-code table (also `gog exit-codes`).
gog completion zsh          # Generate shell completion (bash|zsh|fish|pwsh).
GOG_HELP=full gog --help    # Expanded help with all commands.
```

**Stable exit codes:**

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Generic failure |
| 2 | Usage / parse error |
| 3 | Empty result set (paging) |
| 4 | Auth required (401, keyring miss, auth errors) |
| 5 | Not found (404) |
| 6 | Permission denied (403 non-quota) |
| 7 | Rate limited (403 quota, 429) |
| 8 | Retryable (5xx, timeouts, deadline exceeded) |
| 10 | Config error (e.g. missing OAuth credentials) |
| 130 | Cancelled (SIGINT / context canceled) |

### Sandbox for agent runs

```bash
# Only these top-level groups are callable; everything else errors out.
gog --enable-commands calendar,tasks events --today
GOG_ENABLE_COMMANDS=calendar,tasks gog events --today
```

### Account selection

```bash
gog --account you@example.com events --today
GOG_ACCOUNT=work-alias gog drive ls --max 20

# Set a friendly alias once.
gog auth alias set work you@company.com
```

Reserved alias words: `auto`, `default`. `--account auto` resolves to the default or sole stored account.

---

## Core workflow patterns

### Send a Gmail reply with quoted thread text

```bash
gog gmail drafts create --to alice@example.com \
  --subject "Re: Status" --body "See below." \
  --reply-to-message-id 193a... --quote --json
```

### List today's calendar events as JSON, only a few fields

```bash
gog events --today --json --select "summary,startLocal,endLocal,attendees[].email"
```

### Upload a local file to Drive, replacing an existing Doc

```bash
gog drive upload ./spec.md --replace 1A2b3C... --convert-to doc --json
```

### Read a named range from a spreadsheet

```bash
gog sheets get <spreadsheetId> "Roster" --json --results-only
```

### Batch-modify Gmail label on matching threads

```bash
# Preview first.
gog gmail search "label:inbox older_than:30d" --max 200 --json --select "id" \
  | jq -r '.[].id' \
  | xargs -n1 -I{} gog gmail thread modify {} --add Archive --dry-run

# Then apply.
... (drop --dry-run)
```

### Agent-safe call: JSON, dry-run, explicit account, field projection

```bash
gog --account work --no-input \
    calendar create primary \
    --summary "Focus block" --from "2026-04-17T09:00:00-07:00" \
    --to "2026-04-17T11:00:00-07:00" --event-type focus-time \
    --dry-run --json --results-only
```

---

## Quick command reference

Top-level groups (aliases in parentheses):

| Group | One-liner |
|---|---|
| `gmail` (`mail`, `email`) | Search/read/send, labels, drafts, filters, delegates, vacation, send-as, forwarding, watch, track. |
| `calendar` (`cal`) | Events, calendars, ACL, free/busy, focus-time/OOO/working-location, recurrence, team calendars, respond. |
| `drive` (`drv`) | List/search/upload/download/replace/convert, shares, permissions, shared drives, folders. |
| `docs` (`doc`) | Create/copy/export, tab-aware edit/write/insert/find-replace, Markdown import/export, `sed`-style regex, comments. |
| `slides` (`slide`) | Create/copy/export, add/delete/replace/read slides, speaker notes, Markdown/template-driven decks. |
| `sheets` (`sheet`) | Metadata, get/update/append/clear, find-replace, named ranges, tab management, formatting, merge, freeze. |
| `contacts` (`contact`) | People CRUD with custom fields; other-contacts; Workspace directory. |
| `tasks` (`task`) | Tasklists + tasks; add/done/undo/delete/clear; client-materialized recurrence. |
| `chat` | **Workspace only.** Spaces, messages, threads, DMs, reactions. |
| `classroom` (`class`) | **Workspace-for-Education.** Courses, rosters, coursework, submissions, topics. |
| `forms` (`form`) | Create/update forms and questions, list responses, Pub/Sub watches. |
| `appscript` (`script`, `apps-script`) | Apps Script projects: get/content/create/bind; `run <function>`. |
| `people` (`person`) | OIDC profile (`me`), directory search, relations. |
| `keep` | **Workspace + DWD service account.** Notes and attachments. |
| `admin` | **Workspace + DWD.** Directory users and groups. |
| `groups` (`group`) | Cloud Identity: groups you belong to, group members. |
| `time` | Local/UTC time helpers for scripts and agents. |
| `auth` / `config` / `agent` / `schema` / `completion` / `version` | CLI meta. |

### Desire-path root aliases

These rewrite to the full path:

| Shortcut | Expands to |
|---|---|
| `send` | `gmail send` |
| `ls` / `list` | `drive ls` |
| `search` / `find` | `drive search` |
| `download` / `dl` | `drive download` |
| `upload` / `up` / `put` | `drive upload` |
| `open` / `browse` | `open` (best-effort web URL for a Google ID, offline) |
| `login` | `auth add` |
| `logout` | `auth remove` |
| `status` / `st` | `auth status` |
| `me` / `whoami` / `who-am-i` | `people me` |

---

## Date and time contract

- Prefer **RFC3339** for datetimes (`2026-04-17T09:00:00-07:00`). Timezone offset is required.
- **Date-only** (`YYYY-MM-DD`) is accepted for all-day events, Tasks `--due`, and Contacts `--birthday`.
- Relative words accepted on calendar `--from`/`--to`: `now`, `today`, `tomorrow`, `yesterday`, weekday names (`monday`, `next friday`).
- Durations (Gmail tracking `--since`): Go `time.ParseDuration` format (`15m`, `24h`).
- `GOG_TIMEZONE=<IANA>` (or `local`/`UTC`) or `default_timezone` in `config.json` controls Calendar/Gmail display TZ. IANA DB is embedded, so Windows works.
- Calendar JSON output includes agent-friendly `startDayOfWeek`, `endDayOfWeek`, `timezone`, `eventTimezone`, `startLocal`, `endLocal`.

---

## Advanced usage

Per-surface details, the full command inventory, and agent recipes live in the `references/` directory:

- [references/auth.md](references/auth.md) — OAuth, ADC, service accounts + DWD, least-privilege scope flags, multi-account, keyring backends.
- [references/gmail.md](references/gmail.md) — Search, send, drafts, labels, filters, attachments, watches, `autoreply`, email-open tracking.
- [references/calendar.md](references/calendar.md) — Events, recurrence, free/busy, focus-time/OOO, responding, team calendars, aliases.
- [references/drive.md](references/drive.md) — Listing/search, upload/convert, download with `--format`, sharing, permissions, shared drives.
- [references/sheets.md](references/sheets.md) — Read/write/append, find-replace, tabs, named ranges, formatting, merge, freeze, notes.
- [references/docs-slides.md](references/docs-slides.md) — Docs tab-aware editing, Markdown import/export, `sed`-style edits; Slides creation from Markdown/templates.
- [references/other-surfaces.md](references/other-surfaces.md) — Chat, Contacts, Tasks, People, Admin, Groups, Keep, Forms, Apps Script, Classroom.

---

## Troubleshooting

### Auth

- **`exit 4` (auth required).** Run `gog auth status`; re-run `gog auth add <email>` if the keyring entry is missing. For scope errors, append `--force-consent`.
- **Keychain prompts repeatedly (macOS).** Different binary paths (`go run` rebuilds, `./bin/gog` vs `$(brew --prefix)/bin/gog`) look like different apps to Keychain. Use one stable binary path, or switch backend: `gog auth keyring file` + `GOG_KEYRING_PASSWORD=<pw>`.
- **`--no-input` + `file` keyring backend.** You must set `GOG_KEYRING_PASSWORD`, otherwise the backend fails to unlock.
- **Missing refresh token after OAuth.** Google doesn't re-issue refresh tokens for previously-consented clients. Re-run `gog auth add <email> --force-consent`.
- **Scope errors on Groups.** Re-auth with `gog auth add <email> --services groups --force-consent`.

### Drive

- **`drive ls --all` with `--parent`.** These flags are mutually exclusive.
- **`drive download --format` returns error.** `--format` is Workspace-only (Docs/Sheets/Slides/etc.). Binary user files have no export formats.
- **`drive delete` didn't remove the file.** It trashes by default. Pass `--permanent` to hard-delete (irreversible).
- **Public share confirmation even with `--no-input`.** Public/domain shares and Gmail forwarding filters always confirm; pass `--force` to skip.

### Gmail

- **Label IDs case mismatch.** Gmail label IDs are case-sensitive opaque tokens. Don't lowercase them in filters or `watch serve --exclude-labels`.
- **`--track` failing.** Requires exactly 1 recipient (no cc/bcc) and an HTML body (`--body-html` or `--quote`). Also requires `gog gmail track setup` first.

### Calendar

- **`--from`/`--to` parse errors.** RFC3339 needs a timezone offset. Or use date-only / relative words (`today`, `next monday`).

### Docs

- **Tab-aware commands require `--tab-id`, not a tab name.** Discover IDs with `gog docs list-tabs <docId>`.

### Workspace-only gotchas

- **Chat** needs Google Workspace; consumer `@gmail.com` doesn't work.
- **Classroom** needs Google Workspace for Education.
- **Keep** and **Admin** require a service account with domain-wide delegation (DWD). See [references/auth.md](references/auth.md#service-account--domain-wide-delegation).

### Agent-mode

- **Empty pages on list operations** return exit code **3**, not 0. If you treat "no results" as success, check `exit_code in {0,3}`.
- **`--fields` on `calendar events|ls|list`** forwards to the Calendar API `fields=` partial-response param, not the local `--select` projection. Use `--select` for JSON projection there.
- **`GOG_AUTO_JSON=1` off a TTY only.** If you redirect stderr-only (`2>log`), stdout is still a TTY in most shells; set `--json` explicitly when uncertain.
