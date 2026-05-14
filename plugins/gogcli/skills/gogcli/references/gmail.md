# Gmail — gogcli

All commands live under `gog gmail` (aliases: `mail`, `email`). Root-alias shortcut: `gog send` → `gog gmail send`.

## Table of contents

- [Search and read](#search-and-read)
- [Send](#send)
- [Drafts](#drafts)
- [Labels](#labels)
- [Thread and message modify](#thread-and-message-modify)
- [Filters](#filters)
- [Attachments](#attachments)
- [Settings (vacation, send-as, forwarding, delegates)](#settings-vacation-send-as-forwarding-delegates)
- [Convenience actions](#convenience-actions)
- [Pub/Sub watch](#pubsub-watch)
- [Autoreply](#autoreply)
- [Email-open tracking](#email-open-tracking)

## Search and read

```bash
# Gmail search syntax (newer_than:7d, from:foo, is:unread, has:attachment, label:inbox, ...).
gog gmail search "is:unread newer_than:2d" --max 50 --json
gog gmail search "from:ceo@company.com" --page <TOKEN>
```

Read a single message or full thread:

```bash
gog gmail get <messageId> --format metadata|full|raw
gog gmail thread get <threadId>
gog gmail thread get <threadId> --download --out-dir ./attachments
```

## Send

```bash
gog gmail send --to alice@example.com \
               --subject "Ship it" \
               --body "Merged." \
               --json
```

Flags:

| Flag | Purpose |
|---|---|
| `--to <addr>` | Recipient (required). Can pass multiple for non-track sends. |
| `--cc <addr>` / `--bcc <addr>` | Cc/Bcc. Not compatible with `--track`. |
| `--subject <s>` | Subject. |
| `--body <s>` | Plain-text body. |
| `--body-html <s>` | HTML body (enables rich replies and tracking). |
| `--body-file <path\|->` | Read body from file (or stdin with `-`). |
| `--reply-to-message-id <id>` | Thread the send as a reply. |
| `--quote` | Auto-quote the prior message when replying. |
| `--track` | Add open-tracking pixel. See [Email-open tracking](#email-open-tracking). Requires exactly 1 recipient, HTML body, and `gog gmail track setup` completed first. |
| `--track-split` | Per-recipient tracking IDs. |
| `--attach <path>` | Attach one or more files. |

## Drafts

```bash
gog gmail drafts list
gog gmail drafts create --to alice@example.com --subject "Draft" --body "WIP"
gog gmail drafts update <draftId> --body "Updated"
gog gmail drafts send <draftId>
```

Drafts support `--reply-to-message-id` and `--quote` to prepare threaded replies.

## Labels

Label IDs are **case-sensitive** opaque tokens returned by `labels list`. Don't lowercase them.

```bash
gog gmail labels list --json
gog gmail labels get <labelId>
gog gmail labels create "ProjectX"
gog gmail labels rename <labelId> "Project-X"
gog gmail labels modify <labelId> --color <#hex>
gog gmail labels delete <labelId>
```

## Thread and message modify

```bash
# Whole-thread label changes.
gog gmail thread modify <threadId> --add Label_abc --remove INBOX

# Single-message label changes.
gog gmail messages modify <messageId> --add Label_abc --remove INBOX
```

Both honor `--dry-run`.

## Filters

```bash
gog gmail filters list --json
gog gmail filters create --from boss@company.com --add-label Priority --remove-label INBOX
gog gmail filters delete <filterId>
gog gmail filters export --out filters.json   # Dump JSON to stdout or file.
```

## Attachments

```bash
# From a message ID.
gog gmail attachment <messageId> <attachmentId> --out ./file.pdf

# From a thread (bulk).
gog gmail thread get <threadId> --download --out-dir ./attachments
```

## Settings (vacation, send-as, forwarding, delegates)

```bash
# Vacation responder.
gog gmail vacation get
gog gmail vacation enable --subject "OOO" --body "Back next week" \
    --start 2026-04-20 --end 2026-04-27 --restrict-to-contacts
gog gmail vacation disable

# Send-as identities.
gog gmail sendas list
gog gmail sendas add --address alt@example.com --name "Alt Name" --signature "..."
gog gmail sendas delete alt@example.com

# Forwarding.
gog gmail forwarding list
gog gmail forwarding add forward-to@example.com
gog gmail forwarding verify forward-to@example.com
gog gmail forwarding remove forward-to@example.com

# Auto-forwarding.
gog gmail autoforward get
gog gmail autoforward set forward-to@example.com --disposition leaveInInbox

# Delegates (Workspace only).
gog gmail delegates list
gog gmail delegates add delegate@example.com
gog gmail delegates remove delegate@example.com
```

Public/risky mutations (adding a forwarding address, granting a delegate) force confirmation even under `--no-input`. Pass `--force` to skip.

## Convenience actions

These honor `--dry-run`:

```bash
gog gmail archive <threadId>
gog gmail read <threadId>
gog gmail unread <threadId>
gog gmail trash <threadId>
```

## Pub/Sub watch

Push-notification handler for Gmail changes.

```bash
# Start a watch on the upstream mailbox.
gog gmail watch start --topic projects/<proj>/topics/<topic>

# Run the local HTTP handler that turns Pub/Sub pushes into webhook calls.
gog gmail watch serve \
    --hook-url https://your.service/webhook \
    --verify-oidc --oidc-email push-sa@<proj>.iam.gserviceaccount.com \
    --oidc-audience https://your.service/webhook \
    --exclude-labels SPAM,TRASH \
    --fetch-delay 3s \
    --history-types messageAdded,messageDeleted,labelAdded,labelRemoved

# Inspect / renew / stop / replay history.
gog gmail watch status           # Bearer tokens are redacted unless --show-secrets.
gog gmail watch renew
gog gmail watch stop
gog gmail watch history
```

Auth for incoming push can be OIDC (`--verify-oidc --oidc-email --oidc-audience`) or a shared bearer (`--token <secret>`).

Defaults:

- `--exclude-labels SPAM,TRASH`
- `--fetch-delay 3s`
- `--history-types messageAdded,messageDeleted,labelAdded,labelRemoved`

## Autoreply

Reply once per matching message, then apply a label to dedupe subsequent runs. Added in Unreleased (0.12+).

```bash
gog gmail autoreply --query "is:unread from:support@vendor.com" \
                    --reply-body "Thanks — ticket created." \
                    --label-after Autoreplied \
                    --archive
```

Useful for scripted support-desk flows; always try with `--dry-run` first.

## Email-open tracking

Backed by a Cloudflare Worker. Setup once:

```bash
gog gmail track setup --worker-url https://tracker.your-account.workers.dev
```

Send with tracking:

```bash
gog gmail send --to alice@example.com --subject "Proposal" \
               --body-html "<p>See attached.</p>" \
               --track
```

Constraints for `--track`: exactly 1 recipient (no cc/bcc), HTML body required (`--body-html` or `--quote`).

Check opens:

```bash
gog gmail track status
gog gmail track opens <trackingId>
gog gmail track opens --to alice@example.com --since 24h
```

See `docs/email-tracking.md` and `docs/email-tracking-worker.md` in the upstream repo for the Worker deployment steps.
