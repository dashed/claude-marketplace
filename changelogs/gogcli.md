# Changelog - gogcli

All notable changes to the gogcli skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-04-16

### Added
- Initial addition to marketplace
- SKILL.md documenting the `gog` CLI (gogcli) for driving Google Workspace from the terminal, with strong "Use when..." triggers covering Gmail, Calendar, Drive, Docs, Slides, Sheets, Chat, Tasks, Contacts, Classroom, Forms, Apps Script, Keep, Admin, and Cloud Identity Groups
- Agent-mode essentials: JSON/plain output modes, `--select` field projection, `--dry-run`/`--force`/`--no-input` safety rails, stable exit codes (0-10, 130), `gog schema`, and the `--enable-commands` sandbox
- First-time OAuth setup, multi-account `--account`/aliases, and date/time contract (RFC3339, relative words, `GOG_TIMEZONE`)
- Core workflow patterns: Gmail reply with quoted thread, Calendar JSON queries, Drive upload-with-convert, Sheets named ranges, batch Gmail label modification, agent-safe Calendar create
- Progressive disclosure via `references/` with 7 per-surface guides:
  - `references/auth.md` — OAuth, ADC, service accounts + DWD, scope flags, keyring backends
  - `references/gmail.md` — search, send, drafts, labels, filters, attachments, watches, email-open tracking
  - `references/calendar.md` — events, recurrence, free/busy, focus-time/OOO, team calendars
  - `references/drive.md` — listing/search, upload/convert, download `--format`, sharing, shared drives
  - `references/sheets.md` — read/write/append, find-replace, tabs, named ranges, formatting
  - `references/docs-slides.md` — tab-aware Docs editing, Markdown import/export, Slides from templates
  - `references/other-surfaces.md` — Chat, Contacts, Tasks, People, Admin, Groups, Keep, Forms, Apps Script, Classroom
- Troubleshooting section covering auth (exit 4, keychain prompts, refresh tokens), Drive (`--all` vs `--parent`, `--format` Workspace-only, trash vs `--permanent`), Gmail (label-id casing, `--track` requirements), Calendar (RFC3339 timezone), Docs (`--tab-id`), and agent-mode (empty-page exit 3, `--fields` vs `--select`)
