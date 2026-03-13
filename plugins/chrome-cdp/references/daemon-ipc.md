# Daemon IPC Protocol Reference

## Overview

Each tab runs a persistent background daemon that holds the CDP session open. The daemon communicates via a Unix domain socket using newline-delimited JSON (NDJSON).

## Socket Location

```
/tmp/cdp-<fullTargetId>.sock
```

Where `<fullTargetId>` is the complete target ID (not the shortened prefix from `list`).

## Wire Protocol

Protocol: **newline-delimited JSON** (NDJSON) — one JSON object per line, UTF-8 encoded.

### Request Format

```json
{"id": 1, "cmd": "snap", "args": []}
```

| Field | Type | Description |
|---|---|---|
| `id` | number | Request identifier, echoed in the response |
| `cmd` | string | Command name (see Command List below) |
| `args` | string[] | Command arguments (same as CLI positional args) |

### Response Format

**Success:**
```json
{"id": 1, "ok": true, "result": "<output string>"}
```

**Error:**
```json
{"id": 1, "ok": false, "error": "<error message>"}
```

| Field | Type | Description |
|---|---|---|
| `id` | number | Echoed from the request |
| `ok` | boolean | Whether the command succeeded |
| `result` | string | Command output (only on success) |
| `error` | string | Error message (only on failure) |

## Command List

Commands mirror the CLI. All commands except `list`, `list_raw`, and `stop` operate on the tab the daemon is attached to.

| Command | Args | Description |
|---|---|---|
| `list` | — | List open pages (formatted) |
| `list_raw` | — | List open pages (JSON) |
| `snap` | — | Accessibility tree snapshot |
| `eval` | `[expr]` | Evaluate JavaScript expression |
| `shot` | `[file]` | Screenshot (default: /tmp/screenshot.png) |
| `html` | `[selector]` | Full page or element HTML |
| `nav` | `[url]` | Navigate to URL and wait for load |
| `net` | — | Network resource timing entries |
| `click` | `[selector]` | Click element by CSS selector |
| `clickxy` | `[x, y]` | Click at CSS pixel coordinates |
| `type` | `[text]` | Insert text at current focus |
| `loadall` | `[selector, ms]` | Click "load more" until gone |
| `evalraw` | `[method, json]` | Raw CDP command passthrough |
| `stop` | — | Shut down the daemon |

## Daemon Lifecycle

- **Spawned** automatically on first command to a tab
- **Persists** across commands, keeping the CDP session alive
- **Auto-exits** after 20 minutes of inactivity
- **Shuts down** when the tab is closed or Chrome disconnects
- **Stoppable** via `stop` command or SIGTERM/SIGINT

## Example: Direct Socket Communication

```python
import json
import socket

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/cdp-6BE827FA01234567890ABCDEF.sock")

# Send request
request = {"id": 1, "cmd": "snap", "args": []}
sock.sendall((json.dumps(request) + "\n").encode())

# Read response
data = b""
while b"\n" not in data:
    data += sock.recv(4096)

response = json.loads(data.split(b"\n")[0])
if response["ok"]:
    print(response["result"])
else:
    print("Error:", response["error"])

sock.close()
```

## Notes

- Each daemon holds exactly one CDP session for one tab.
- The `id` field is optional but recommended for matching responses to requests.
- The `list` and `list_raw` commands can be sent to any daemon — they query Chrome's target list, not just the attached tab.
- Use `evalraw` to access any CDP domain method not covered by the built-in commands.
