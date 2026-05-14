---
name: chrome-cdp
description: Interact with local Chrome browser session via Chrome DevTools Protocol. Use when asked to inspect, debug, or interact with a page open in Chrome, take screenshots of browser tabs, read accessibility trees, evaluate JavaScript, click elements, navigate pages, or automate browser interactions in a live Chrome session.
---

# Chrome CDP

Lightweight Chrome DevTools Protocol CLI. Connects directly via WebSocket — no Puppeteer, works with 100+ tabs, instant connection. Uses a persistent per-tab daemon so Chrome's "Allow debugging" modal fires only once.

## Prerequisites

- Chrome with remote debugging enabled: open `chrome://inspect/#remote-debugging` and toggle the switch
- Python 3.10+ with `websockets` library

## Commands

All commands use `python -m chrome_cdp`. The `<target>` is a **unique** targetId prefix from `list`; copy the full prefix shown in the `list` output (for example `6BE827FA`). The CLI rejects ambiguous prefixes.

### List open pages

```bash
python -m chrome_cdp list
```

### Take a screenshot

```bash
python -m chrome_cdp shot <target> [file]    # default: /tmp/screenshot.png
```

Captures the **viewport only**. Scroll first with `eval` if you need content below the fold. Output includes the page's DPR and coordinate conversion hint (see [references/coordinate-system.md](references/coordinate-system.md)).

### Accessibility tree snapshot

```bash
python -m chrome_cdp snap <target>
```

Prefer `snap` over `html` for understanding page structure — it's compact and semantic.

### Evaluate JavaScript

```bash
python -m chrome_cdp eval <target> <expr>
```

> **Watch out:** avoid index-based selection (`querySelectorAll(...)[i]`) across multiple `eval` calls when the DOM can change between them (e.g. after clicking Ignore, card indices shift). Collect all data in one `eval` or use stable selectors.

### Other commands

```bash
python -m chrome_cdp html    <target> [selector]   # full page or element HTML
python -m chrome_cdp nav     <target> <url>         # navigate and wait for load
python -m chrome_cdp net     <target>               # resource timing entries
python -m chrome_cdp click   <target> <selector>    # click element by CSS selector
python -m chrome_cdp clickxy <target> <x> <y>       # click at CSS pixel coords
python -m chrome_cdp type    <target> <text>         # Input.insertText at current focus
python -m chrome_cdp loadall <target> <selector> [ms]  # click "load more" until gone
python -m chrome_cdp evalraw <target> <method> [json]  # raw CDP command passthrough
python -m chrome_cdp stop    [target]               # stop daemon(s)
```

## Coordinates

`shot` saves an image at native resolution: image pixels = CSS pixels x DPR. CDP Input events (`clickxy` etc.) take **CSS pixels**.

```
CSS px = screenshot image px / DPR
```

`shot` prints the DPR for the current page. Typical Retina (DPR=2): divide screenshot coords by 2.

For the full coordinate system reference including DPR detection, viewer scaling, and worked examples, see [references/coordinate-system.md](references/coordinate-system.md).

## Tips

- Prefer `snap` over `html` for page structure — it's compact and semantic.
- Use `type` (not eval) to enter text in cross-origin iframes — use `click`/`clickxy` to focus first, then `type`.
- Chrome shows an "Allow debugging" modal once per tab on first access. A background daemon keeps the session alive so subsequent commands need no further approval. Daemons auto-exit after 20 minutes of inactivity.
- Use `evalraw` to send arbitrary CDP methods not covered by the built-in commands (e.g. `DOM.getDocument`, `Network.enable`).

## Advanced Usage

For detailed protocol documentation, see:
- [references/coordinate-system.md](references/coordinate-system.md) — DPR, CSS pixels, screenshot coordinate mapping
- [references/daemon-ipc.md](references/daemon-ipc.md) — Unix socket protocol, NDJSON format, request/response schema
