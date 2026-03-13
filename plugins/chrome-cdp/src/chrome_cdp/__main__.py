"""CLI entry point for chrome-cdp — lightweight Chrome DevTools Protocol CLI."""

from __future__ import annotations

import asyncio
import json
import sys

from .client import CDPClient
from .commands import format_page_list, get_pages
from .daemon import (
    connect_to_socket,
    find_any_daemon_socket,
    get_or_start_tab_daemon,
    run_daemon,
    send_command,
    stop_daemons,
)
from .helpers import (
    PAGES_CACHE,
    get_ws_url,
    list_daemon_sockets,
    resolve_prefix,
)

USAGE = """\
cdp - lightweight Chrome DevTools Protocol CLI (no Puppeteer)

Usage: cdp <command> [args]

  list                              List open pages (shows unique target prefixes)
  snap  <target>                    Accessibility tree snapshot
  eval  <target> <expr>             Evaluate JS expression
  shot  <target> [file]             Screenshot (default: /tmp/screenshot.png)
  html  <target> [selector]         Get HTML (full page or CSS selector)
  nav   <target> <url>              Navigate to URL and wait for load completion
  net   <target>                    Network performance entries
  click   <target> <selector>       Click an element by CSS selector
  clickxy <target> <x> <y>          Click at CSS pixel coordinates (see coordinate note below)
  type    <target> <text>           Type text at current focus via Input.insertText
                                    Works in cross-origin iframes unlike eval-based approaches
  loadall <target> <selector> [ms]  Repeatedly click a "load more" button until it disappears
                                    Optional interval in ms between clicks (default 1500)
  evalraw <target> <method> [json]  Send a raw CDP command; returns JSON result
                                    e.g. evalraw <t> "DOM.getDocument" '{}'
  stop  [target]                    Stop daemon(s)

<target> is a unique targetId prefix from "cdp list". If a prefix is ambiguous,
use more characters.

COORDINATE SYSTEM
  shot captures the viewport at the device's native resolution.
  The screenshot image size = CSS pixels \u00d7 DPR (device pixel ratio).
  For CDP Input events (clickxy, etc.) you need CSS pixels, not image pixels.

    CSS pixels = screenshot image pixels / DPR

  shot prints the DPR and an example conversion for the current page.
  Typical Retina (DPR=2): CSS px \u2248 screenshot px \u00d7 0.5
  If your viewer rescales the image further, account for that scaling too.

EVAL SAFETY NOTE
  Avoid index-based DOM selection (querySelectorAll(...)[i]) across multiple
  eval calls when the list can change between calls (e.g. after clicking
  "Ignore" buttons on a feed \u2014 indices shift). Prefer stable selectors or
  collect all data in a single eval.

DAEMON IPC (for advanced use / scripting)
  Each tab runs a persistent daemon at Unix socket: /tmp/cdp-<fullTargetId>.sock
  Protocol: newline-delimited JSON (one JSON object per line, UTF-8).
    Request:  {"id":<number>, "cmd":"<command>", "args":["arg1","arg2",...]}
    Response: {"id":<number>, "ok":true,  "result":"<string>"}
           or {"id":<number>, "ok":false, "error":"<message>"}
  Commands mirror the CLI: snap, eval, shot, html, nav, net, click, clickxy,
  type, loadall, evalraw, stop. Use evalraw to send arbitrary CDP methods.
  The socket disappears after 20 min of inactivity or when the tab closes.
"""

NEEDS_TARGET = {
    "snap",
    "snapshot",
    "eval",
    "shot",
    "screenshot",
    "html",
    "nav",
    "navigate",
    "net",
    "network",
    "click",
    "clickxy",
    "type",
    "loadall",
    "evalraw",
}


async def main() -> None:
    """Main CLI entry point (async)."""
    argv = sys.argv[1:]
    cmd = argv[0] if argv else None
    args = argv[1:] if len(argv) > 1 else []

    # Daemon mode (internal)
    if cmd == "_daemon":
        await run_daemon(args[0])
        return

    if not cmd or cmd in ("help", "--help", "-h"):
        print(USAGE)
        sys.exit(0)

    # List — use existing daemon if available, otherwise direct
    if cmd in ("list", "ls"):
        pages = None
        existing_sock = find_any_daemon_socket()
        if existing_sock:
            try:
                reader, writer = await connect_to_socket(existing_sock)
                resp = await send_command(reader, writer, {"cmd": "list_raw"})
                if resp.get("ok"):
                    pages = json.loads(resp["result"])
            except Exception:
                pass
        if pages is None:
            # No daemon running — connect directly (will trigger one Allow)
            cdp = CDPClient()
            await cdp.connect(get_ws_url())
            pages = await get_pages(cdp)
            await cdp.close()
        PAGES_CACHE.write_text(json.dumps(pages))
        print(format_page_list(pages))
        return

    # Stop
    if cmd == "stop":
        await stop_daemons(args[0] if args else None)
        return

    # Page commands — need target prefix
    if cmd not in NEEDS_TARGET:
        print(f"Unknown command: {cmd}\n", file=sys.stderr)
        print(USAGE)
        sys.exit(1)

    target_prefix: str | None = args[0] if args else None
    if not target_prefix:
        print('Error: target ID required. Run "cdp list" first.', file=sys.stderr)
        sys.exit(1)

    assert target_prefix is not None  # narrowing for type checker after sys.exit

    # Resolve prefix -> full targetId from cache or running daemon
    daemon_target_ids = [d["target_id"] for d in list_daemon_sockets()]
    daemon_matches = [
        tid for tid in daemon_target_ids if tid.upper().startswith(target_prefix.upper())
    ]

    if daemon_matches:
        target_id = resolve_prefix(target_prefix, daemon_target_ids, "daemon")
    else:
        if not PAGES_CACHE.exists():
            print('No page list cached. Run "cdp list" first.', file=sys.stderr)
            sys.exit(1)
        pages = json.loads(PAGES_CACHE.read_text())
        target_id = resolve_prefix(
            target_prefix, [p["targetId"] for p in pages], "target", 'Run "cdp list".'
        )

    reader, writer = await get_or_start_tab_daemon(target_id)

    cmd_args = args[1:]

    if cmd == "eval":
        expr = " ".join(cmd_args)
        if not expr:
            print("Error: expression required", file=sys.stderr)
            sys.exit(1)
        cmd_args = [expr]
    elif cmd == "type":
        text = " ".join(cmd_args)
        if not text:
            print("Error: text required", file=sys.stderr)
            sys.exit(1)
        cmd_args = [text]
    elif cmd == "evalraw":
        if not cmd_args:
            print("Error: CDP method required", file=sys.stderr)
            sys.exit(1)
        if len(cmd_args) > 2:
            cmd_args = [cmd_args[0], " ".join(cmd_args[1:])]

    if cmd in ("nav", "navigate") and not cmd_args:
        print("Error: URL required", file=sys.stderr)
        sys.exit(1)

    response = await send_command(reader, writer, {"cmd": cmd, "args": cmd_args})

    if response.get("ok"):
        if response.get("result"):
            print(response["result"])
    else:
        print(f"Error: {response.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


def main_sync() -> None:
    """Synchronous entry point for console_scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
