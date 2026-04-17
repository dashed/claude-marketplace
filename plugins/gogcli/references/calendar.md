# Calendar — gogcli

All commands live under `gog calendar` (alias `cal`). There is no top-level `events` command — but `gog calendar events` is the primary listing entry point.

## Table of contents

- [Calendars and discovery](#calendars-and-discovery)
- [Listing events](#listing-events)
- [Reading a single event](#reading-a-single-event)
- [Searching events](#searching-events)
- [Creating events](#creating-events)
- [Updating events](#updating-events)
- [Deleting events](#deleting-events)
- [Responding to invitations](#responding-to-invitations)
- [Free/busy and conflicts](#freebusy-and-conflicts)
- [Focus time, OOO, working location](#focus-time-ooo-working-location)
- [Calendar aliases and subscriptions](#calendar-aliases-and-subscriptions)
- [ACLs, colors, proposing time](#acls-colors-proposing-time)
- [Date/time conventions](#datetime-conventions)

## Calendars and discovery

```bash
gog calendar calendars               # List accessible calendars.
gog calendar calendars --json
```

The returned list includes numeric indices usable in `--calendars 1,3` on other subcommands.

## Listing events

```bash
# Default: primary calendar, upcoming.
gog calendar events

# Time windows.
gog calendar events --today
gog calendar events --tomorrow
gog calendar events --week
gog calendar events --days 14
gog calendar events --from 2026-04-15 --to 2026-04-22

# All events (skip automatic upcoming filter).
gog calendar events --all

# Multiple calendars.
gog calendar events --calendars 1,3
gog calendar events --cal "Team Standups"

# Day-of-week columns in table output.
gog calendar events --week --weekday
```

Flags accept RFC3339, date-only, or relative words (`today`, `friday`, `next monday`).

**Remember:** For `calendar events|ls|list`, `--fields` is the Calendar API `fields=` partial-response selector, not the generic projector. Use `--select` to project JSON output.

## Reading a single event

```bash
gog calendar event <calendarId> <eventId>
gog calendar get   <calendarId> <eventId>  # alias
```

JSON output includes `startDayOfWeek`, `endDayOfWeek`, `timezone`, `eventTimezone`, `startLocal`, `endLocal` to simplify agent scheduling.

## Searching events

```bash
gog calendar search "design review" --max 25
gog calendar search "1:1" --from "next monday" --to "next friday"
gog calendar search "offsite" --days 30 --json
```

Default window is `−30d → +90d` when no range is given.

## Creating events

```bash
gog calendar create primary \
    --summary "Design review" \
    --from "2026-04-17T10:00:00-07:00" \
    --to   "2026-04-17T11:00:00-07:00" \
    --attendees alice@example.com,bob@example.com \
    --location "HQ / Zoom" \
    --rrule "RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=6" \
    --reminder email:3d \
    --reminder popup:30m \
    --send-updates all \
    --json
```

| Flag | Purpose |
|---|---|
| `--summary` | Event title. |
| `--from` / `--to` | RFC3339 (tz required), date-only for `--all-day`, or relative words. |
| `--all-day` | All-day event; use date-only for `--from`/`--to`. |
| `--attendees <csv>` | Invite attendees (also `--add-attendee` on `update`). |
| `--location` | Location string. |
| `--rrule "RRULE:..."` | Recurrence. Standard iCal RRULE. |
| `--reminder <method>:<offset>` | e.g. `email:3d`, `popup:30m`. Repeatable. |
| `--send-updates <all\|externalOnly\|none>` | Invitation emails policy. |
| `--event-type <focus-time\|out-of-office\|working-location>` | Specialized event type. |
| `--description <text>` | Long description. |

## Updating events

```bash
# Update a single instance of a recurring event.
gog calendar update primary <eventId> --scope single --summary "Renamed"

# Update this and future instances.
gog calendar update primary <eventId> --scope future --location "New HQ"

# Update the whole series.
gog calendar update primary <eventId> --scope all --summary "Quarterly planning"

# Add an attendee without touching anything else.
gog calendar update primary <eventId> --add-attendee vip@example.com --send-updates externalOnly
```

`--scope future` on an instance event ID resolves to the correct parent recurrence internally. Updates preserve RRULE and timezone unless explicitly overridden.

## Deleting events

```bash
gog calendar delete primary <eventId>
gog calendar delete primary <eventId> --scope future --send-updates all --force
```

Honors `--dry-run`. `--force` skips the confirmation prompt.

## Responding to invitations

```bash
gog calendar respond primary <eventId> --status accepted
gog calendar respond primary <eventId> --status tentative --send-updates all
gog calendar respond primary <eventId> --status declined
```

## Free/busy and conflicts

```bash
gog calendar freebusy --calendars primary,alice@example.com \
                      --from "2026-04-15T09:00:00-07:00" \
                      --to   "2026-04-15T17:00:00-07:00"

gog calendar conflicts --today
gog calendar conflicts --all --cal "Team Calendar" --today
```

## Focus time, OOO, working location

Opinionated shortcuts — these skip boilerplate `--event-type` flags.

```bash
gog calendar focus-time --from "2026-04-17T09:00:00-07:00" --to "2026-04-17T11:00:00-07:00"

gog calendar out-of-office --from 2026-04-20 --to 2026-04-22 --message "On vacation"

gog calendar working-location --today --location home
gog calendar working-location --today --location office --office-name "HQ"
```

## Calendar aliases and subscriptions

```bash
# Local aliases resolved by --cal or --calendars.
gog calendar alias list
gog calendar alias set "Team" team-cal@group.calendar.google.com
gog calendar alias unset "Team"

# Subscribe to an additional public/team calendar.
gog calendar subscribe team-cal@group.calendar.google.com

# Shortcut: list events across members of a Workspace group.
gog calendar team engineering@company.com --today
```

## ACLs, colors, proposing time

```bash
gog calendar acl primary                           # List ACL rules.
gog calendar users <calendarId>                    # Users with access.
gog calendar colors                                # Color palette reference.
gog calendar propose-time primary <eventId> \
    --from "2026-04-18T10:00:00-07:00" --to "2026-04-18T10:30:00-07:00"
```

## Date/time conventions

- RFC3339 requires a timezone offset. Use `GOG_TIMEZONE=<IANA>` to make `--json` output use a specific display timezone.
- Date-only works for `--all-day` and for range flags when listing.
- Relative words for `--from`/`--to`: `now`, `today`, `tomorrow`, `yesterday`, weekday names, `next monday`, etc.
- Calendar JSON output includes `startLocal`, `endLocal`, `startDayOfWeek`, `endDayOfWeek`, `timezone`, `eventTimezone` — prefer these in agent logic over re-parsing UTC strings.
