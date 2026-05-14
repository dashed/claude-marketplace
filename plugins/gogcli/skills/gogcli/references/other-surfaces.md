# Other Google surfaces — gogcli

Quick-reference for the remaining command groups. Most inherit the same global flags (`--json`, `--plain`, `--select`, `--dry-run`, `--force`, `--no-input`, `--account`, `--client`, `--access-token`, `--verbose`).

## Table of contents

- [Chat (Workspace only)](#chat-workspace-only)
- [Contacts](#contacts)
- [Tasks](#tasks)
- [People](#people)
- [Admin (Workspace, DWD)](#admin-workspace-dwd)
- [Cloud Identity Groups](#cloud-identity-groups)
- [Keep (Workspace, DWD)](#keep-workspace-dwd)
- [Forms](#forms)
- [Apps Script](#apps-script)
- [Classroom (EDU only)](#classroom-edu-only)
- [Time helpers](#time-helpers)

## Chat (Workspace only)

Consumer `@gmail.com` accounts are not supported.

```bash
# Spaces.
gog chat spaces list --json
gog chat spaces find "Platform"
gog chat spaces create "Design Reviews" --member alice@co.com --member bob@co.com

# Messages.
gog chat messages list spaces/<spaceId> --max 50
gog chat messages list spaces/<spaceId> --thread <threadName> --unread
gog chat messages send spaces/<spaceId> --text "PR merged." \
                                         --thread spaces/<spaceId>/threads/<threadId>

# Reactions.
gog chat messages react <messageName> 🎉
gog chat messages reactions list   <messageName>
gog chat messages reactions create <messageName> --emoji 👍
gog chat messages reactions delete <reactionName>

# Threads.
gog chat threads list spaces/<spaceId>

# Direct messages.
gog chat dm space user@co.com
gog chat dm send  user@co.com --text "ping"
```

## Contacts

```bash
# List + search.
gog contacts list --max 100 --json
gog contacts search "alice"

# Read one (resource name `people/<id>` or an email address).
gog contacts get people/c123
gog contacts get alice@example.com

# Create with rich fields.
gog contacts create \
    --given "Alice" --family "Ng" \
    --email alice@example.com \
    --phone "+1-555-0123" \
    --address "100 Main St, SF" \
    --org "Example Corp" --title "Engineer" \
    --url "https://example.com/alice" \
    --note "Met at QCon 2026" \
    --custom "Pronouns=she/her" \
    --relation "spouse=people/c456" \
    --birthday 1990-02-14

# Update (same flags) or pipe a JSON edit.
gog contacts update people/c123 --title "Senior Engineer"

gog contacts get people/c123 --json \
  | jq '.emails[0].value = "alice@new.com"' \
  | gog contacts update people/c123 --from-file -

gog contacts delete people/c123

# Other-contacts (seen via email).
gog contacts other list
gog contacts other search "vendor"

# Workspace directory (requires Workspace).
gog contacts directory list
gog contacts directory search "onboarding"
```

## Tasks

```bash
gog tasks lists --max 10 --json
gog tasks lists create "Inbox"

# List items in a tasklist.
gog tasks list <tasklistId> --max 50
gog tasks get  <tasklistId> <taskId>

# Add with simple recurrence (materialized client-side).
gog tasks add <tasklistId> --title "Weekly report" \
    --due 2026-04-19 --notes "Slides + numbers" \
    --repeat weekly --repeat-count 4

# Add with an explicit RRULE (also materialized client-side).
gog tasks add <tasklistId> --title "Stand-up prep" \
    --recur-rrule "FREQ=DAILY;INTERVAL=1;BYDAY=MO,TU,WE,TH,FR" \
    --repeat-until 2026-06-30

# Update / done / undo / delete.
gog tasks update <tasklistId> <taskId> --title "Weekly status report"
gog tasks done   <tasklistId> <taskId>
gog tasks undo   <tasklistId> <taskId>
gog tasks delete <tasklistId> <taskId>

# Clear all completed tasks from a list.
gog tasks clear <tasklistId>
```

Google Tasks API has **no server-side recurring metadata** — `--repeat` / `--recur-rrule` create concrete occurrences up to the configured horizon.

## People

```bash
gog people me --json              # Also: gog me, gog whoami, gog who-am-i.
gog people search "alice"          # Directory search (Workspace features require Workspace).
gog people relations <peopleId>
```

## Admin (Workspace, DWD)

Requires a domain-wide-delegation service account with Admin SDK Directory scopes allowlisted in Workspace Admin.

```bash
# Directory users.
gog admin users list --max 100 --json
gog admin users get alice@company.com
gog admin users create --email alice@company.com --given "Alice" --family "Ng" \
                       --password "<temp>" --change-password
gog admin users suspend alice@company.com --reason "off-boarding"

# Groups.
gog admin groups list --json
gog admin groups add    engineering@company.com --member alice@company.com
gog admin groups remove engineering@company.com --member alice@company.com
```

See [auth.md](auth.md#service-account--domain-wide-delegation) for DWD setup.

## Cloud Identity Groups

Different API surface from `admin groups` (Cloud Identity vs Admin SDK). OAuth scopes only, no DWD required — but re-auth is needed:

```bash
gog auth add you@example.com --services groups --force-consent

gog groups list --json                      # Groups you belong to.
gog groups members <groupEmail> --max 100
```

## Keep (Workspace, DWD)

Requires a service account with domain-wide delegation; the Keep scope must be registered in the Workspace DWD allowlist. Since 0.12 the Keep SA fallback is isolated to Keep commands — it won't leak into Gmail/Drive/etc.

```bash
gog keep notes list --max 50 --json
gog keep notes get <noteId>
gog keep notes search "retro"

gog keep notes create --title "Retro notes" --body "Went well..." --label retro

gog keep notes delete <noteId>

# Attachments on a note.
gog keep notes attachments <noteId> --json
```

## Forms

```bash
# Create / inspect / update a form.
gog forms create "Event signup"
gog forms get <formId> --json
gog forms update <formId> --title "Updated event signup"

# Questions.
gog forms add-question <formId> --type text --title "Name"
gog forms add-question <formId> --type multiple-choice --title "Track" \
                               --option "Eng" --option "Design" --option "PM"
gog forms delete-question <formId> <itemId> --dry-run
gog forms delete-question <formId> <itemId> --force

# Responses.
gog forms responses list <formId> --max 500 --json
gog forms responses get  <formId> <responseId>

# Pub/Sub watch.
gog forms watch create <formId> --topic projects/<proj>/topics/<topic>
gog forms watch list   <formId>
gog forms watch renew  <formId> <watchId>
gog forms watch delete <formId> <watchId>
```

## Apps Script

```bash
# Inspect / fetch code.
gog appscript get     <scriptId> --json
gog appscript content <scriptId> --out ./src/

# Standalone project.
gog appscript create "Utility script"

# Container-bound project (bound to a Sheet/Doc/Form).
gog appscript bind <containerId> "Sheet script"

# Run a function. Requires an executable deployment and OAuth scopes covering the
# APIs the function touches (Apps Script API enabled, "Run as user", etc.).
gog appscript run <scriptId> <functionName> --param '"hello"' --param "123"
```

Aliases: `gog script`, `gog apps-script`.

## Classroom (EDU only)

Requires Google Workspace for Education.

```bash
gog classroom courses list
gog classroom courses get <courseId>

gog classroom rosters students <courseId>
gog classroom rosters teachers <courseId>

gog classroom coursework list <courseId>
gog classroom coursework get  <courseId> <workId>

gog classroom submissions list <courseId> <workId>
gog classroom submissions get  <courseId> <workId> <submissionId>

gog classroom announcements list <courseId>
gog classroom topics list        <courseId>
gog classroom invitations list   <courseId>
gog classroom guardians list     <studentId>

gog classroom profiles get       <userId>
gog classroom materials list     <courseId>
```

Alias: `gog class`.

## Time helpers

Convenience utilities for scripts and agents that need consistent timestamps across surfaces.

```bash
gog time now                # RFC3339 local time.
gog time now --utc
gog time now --format 2006-01-02
gog time parse "next friday"   # Shows the resolved absolute time.
gog time diff "2026-04-17T09:00:00-07:00" "2026-04-17T11:30:00-07:00"
```

Exact subcommands depend on the installed version; run `gog time --help` to list them.
