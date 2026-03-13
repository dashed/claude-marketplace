"""Per-tab daemon — holds a CDP session open over a Unix socket."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import signal
import subprocess
import sys
from typing import Any

from .client import CDPClient
from .commands import (
    click_str,
    click_xy_str,
    eval_raw_str,
    eval_str,
    format_page_list,
    get_pages,
    html_str,
    load_all_str,
    nav_str,
    net_str,
    shot_str,
    snapshot_str,
    type_str,
)
from .helpers import (
    DAEMON_CONNECT_DELAY,
    DAEMON_CONNECT_RETRIES,
    IDLE_TIMEOUT,
    get_ws_url,
    list_daemon_sockets,
    resolve_prefix,
    sock_path,
)


async def _handle_command(
    cdp: CDPClient,
    session_id: str,
    cmd: str,
    args: list[str],
) -> dict[str, Any]:
    """Dispatch a command and return a response dict."""
    try:
        result: str | None = None
        if cmd == "list":
            pages = await get_pages(cdp)
            result = format_page_list(pages)
        elif cmd == "list_raw":
            pages = await get_pages(cdp)
            result = json.dumps(pages)
        elif cmd in ("snap", "snapshot"):
            result = await snapshot_str(cdp, session_id, compact=True)
        elif cmd == "eval":
            result = await eval_str(cdp, session_id, args[0])
        elif cmd in ("shot", "screenshot"):
            result = await shot_str(cdp, session_id, args[0] if args else None)
        elif cmd == "html":
            result = await html_str(cdp, session_id, args[0] if args else None)
        elif cmd in ("nav", "navigate"):
            result = await nav_str(cdp, session_id, args[0])
        elif cmd in ("net", "network"):
            result = await net_str(cdp, session_id)
        elif cmd == "click":
            result = await click_str(cdp, session_id, args[0])
        elif cmd == "clickxy":
            result = await click_xy_str(cdp, session_id, args[0], args[1])
        elif cmd == "type":
            result = await type_str(cdp, session_id, args[0])
        elif cmd == "loadall":
            interval = int(args[1]) if len(args) > 1 else 1500
            result = await load_all_str(cdp, session_id, args[0], interval)
        elif cmd == "evalraw":
            result = await eval_raw_str(
                cdp, session_id, args[0], args[1] if len(args) > 1 else None
            )
        elif cmd == "stop":
            return {"ok": True, "result": "", "stop_after": True}
        else:
            return {"ok": False, "error": f"Unknown command: {cmd}"}
        return {"ok": True, "result": result or ""}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def run_daemon(target_id: str) -> None:
    """Run a persistent daemon for a single Chrome tab.

    Connects to Chrome via CDP, attaches to the target, and listens on a Unix
    socket for NDJSON commands. Auto-exits after 20 min idle.
    """
    sp = sock_path(target_id)
    shutdown_event = asyncio.Event()

    cdp = CDPClient()
    try:
        await cdp.connect(get_ws_url())
    except Exception as e:
        sys.stderr.write(f"Daemon: cannot connect to Chrome: {e}\n")
        sys.exit(1)

    try:
        res = await cdp.send("Target.attachToTarget", {"targetId": target_id, "flatten": True})
        session_id: str = res["sessionId"]
    except Exception as e:
        sys.stderr.write(f"Daemon: attach failed: {e}\n")
        await cdp.close()
        sys.exit(1)

    server: asyncio.AbstractServer | None = None

    def shutdown() -> None:
        shutdown_event.set()

    # Exit if target goes away or Chrome disconnects
    def _on_target_destroyed(params: dict[str, Any], _: Any) -> None:
        if params.get("targetId") == target_id:
            shutdown()

    def _on_detached(params: dict[str, Any], _: Any) -> None:
        if params.get("sessionId") == session_id:
            shutdown()

    cdp.on_event("Target.targetDestroyed", _on_target_destroyed)
    cdp.on_event("Target.detachedFromTarget", _on_detached)
    cdp.on_close(shutdown)

    # Idle timer
    idle_handle: asyncio.TimerHandle | None = None

    def reset_idle() -> None:
        nonlocal idle_handle
        if idle_handle:
            idle_handle.cancel()
        loop = asyncio.get_event_loop()
        idle_handle = loop.call_later(IDLE_TIMEOUT, shutdown)

    reset_idle()

    # Handle signal-based shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown)

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle a single client connection on the Unix socket."""
        buf = ""
        try:
            while not shutdown_event.is_set():
                data = await reader.read(65536)
                if not data:
                    break
                buf += data.decode()
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        req = json.loads(line)
                    except json.JSONDecodeError:
                        err = {"ok": False, "error": "Invalid JSON request", "id": None}
                        writer.write((json.dumps(err) + "\n").encode())
                        await writer.drain()
                        continue

                    reset_idle()
                    result = await _handle_command(
                        cdp, session_id, req.get("cmd", ""), req.get("args", [])
                    )
                    result["id"] = req.get("id")
                    payload = json.dumps(result) + "\n"
                    writer.write(payload.encode())
                    await writer.drain()

                    if result.get("stop_after"):
                        writer.close()
                        await writer.wait_closed()
                        shutdown()
                        return
        except (ConnectionError, asyncio.CancelledError):
            pass
        finally:
            if not writer.is_closing():
                writer.close()
                with contextlib.suppress(Exception):
                    await writer.wait_closed()

    # Clean up stale socket
    with contextlib.suppress(OSError):
        os.unlink(sp)

    server = await asyncio.start_unix_server(handle_client, path=sp)

    # Wait for shutdown
    await shutdown_event.wait()

    # Cleanup
    if idle_handle:
        idle_handle.cancel()
    server.close()
    await server.wait_closed()
    with contextlib.suppress(OSError):
        os.unlink(sp)
    await cdp.close()


async def connect_to_socket(sp: str) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Connect to a daemon's Unix socket."""
    return await asyncio.open_unix_connection(sp)


async def get_or_start_tab_daemon(
    target_id: str,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Connect to an existing daemon or spawn a new one."""
    sp = sock_path(target_id)

    # Try existing daemon
    try:
        return await connect_to_socket(sp)
    except (ConnectionRefusedError, FileNotFoundError, OSError):
        pass

    # Clean stale socket
    with contextlib.suppress(OSError):
        os.unlink(sp)

    # Spawn daemon
    subprocess.Popen(
        [sys.executable, "-m", "chrome_cdp", "_daemon", target_id],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for socket (includes time for user to click Allow)
    for _ in range(DAEMON_CONNECT_RETRIES):
        await asyncio.sleep(DAEMON_CONNECT_DELAY)
        try:
            return await connect_to_socket(sp)
        except (ConnectionRefusedError, FileNotFoundError, OSError):
            pass

    raise RuntimeError("Daemon failed to start — did you click Allow in Chrome?")


async def send_command(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    req: dict[str, Any],
) -> dict[str, Any]:
    """Send a command to a daemon over its Unix socket and wait for the response."""
    req["id"] = 1
    writer.write((json.dumps(req) + "\n").encode())
    await writer.drain()

    line = await reader.readline()
    if not line:
        raise RuntimeError("Connection closed before response")

    writer.close()
    await writer.wait_closed()
    return json.loads(line)


def find_any_daemon_socket() -> str | None:
    """Find any running daemon socket to reuse for listing pages."""
    sockets = list_daemon_sockets()
    return sockets[0]["socket_path"] if sockets else None


async def stop_daemons(target_prefix: str | None = None) -> None:
    """Stop one or all running daemons."""
    daemons = list_daemon_sockets()

    if target_prefix:
        target_id = resolve_prefix(target_prefix, [d["target_id"] for d in daemons], "daemon")
        daemon = next(d for d in daemons if d["target_id"] == target_id)
        try:
            reader, writer = await connect_to_socket(daemon["socket_path"])
            await send_command(reader, writer, {"cmd": "stop"})
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(daemon["socket_path"])
        return

    for daemon in daemons:
        try:
            reader, writer = await connect_to_socket(daemon["socket_path"])
            await send_command(reader, writer, {"cmd": "stop"})
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(daemon["socket_path"])
