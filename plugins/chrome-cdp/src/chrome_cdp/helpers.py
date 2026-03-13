"""Pure utility functions and constants for chrome-cdp."""

from __future__ import annotations

import os
from pathlib import Path

# Timeouts (milliseconds → seconds for asyncio)
TIMEOUT = 15.0
NAVIGATION_TIMEOUT = 30.0
IDLE_TIMEOUT = 20 * 60  # 20 minutes in seconds

DAEMON_CONNECT_RETRIES = 20
DAEMON_CONNECT_DELAY = 0.3  # seconds
MIN_TARGET_PREFIX_LEN = 8

SOCK_PREFIX = "/tmp/cdp-"
PAGES_CACHE = Path("/tmp/cdp-pages.json")


def sock_path(target_id: str) -> str:
    """Return the Unix socket path for a given target ID."""
    return f"{SOCK_PREFIX}{target_id}.sock"


def get_ws_url() -> str:
    """Read Chrome's DevToolsActivePort file and return the WebSocket URL."""
    port_file = Path.home() / "Library/Application Support/Google/Chrome/DevToolsActivePort"
    lines = port_file.read_text().strip().split("\n")
    return f"ws://127.0.0.1:{lines[0]}{lines[1]}"


def list_daemon_sockets() -> list[dict[str, str]]:
    """List all active daemon Unix sockets in /tmp."""
    result: list[dict[str, str]] = []
    try:
        for f in os.listdir("/tmp"):
            if f.startswith("cdp-") and f.endswith(".sock"):
                result.append(
                    {
                        "target_id": f[4:-5],
                        "socket_path": f"/tmp/{f}",
                    }
                )
    except OSError:
        pass
    return result


def resolve_prefix(
    prefix: str,
    candidates: list[str],
    noun: str = "target",
    missing_hint: str = "",
) -> str:
    """Resolve a prefix to a unique full ID from candidates.

    Raises an error if the prefix matches zero or multiple candidates.
    """
    upper = prefix.upper()
    matches = [c for c in candidates if c.upper().startswith(upper)]
    if len(matches) == 0:
        hint = f" {missing_hint}" if missing_hint else ""
        raise ValueError(f'No {noun} matching prefix "{prefix}".{hint}')
    if len(matches) > 1:
        raise ValueError(
            f'Ambiguous prefix "{prefix}" — matches {len(matches)} {noun}s. Use more characters.'
        )
    return matches[0]


def get_display_prefix_length(target_ids: list[str]) -> int:
    """Find the minimum prefix length to uniquely identify all target IDs."""
    if not target_ids:
        return MIN_TARGET_PREFIX_LEN
    max_len = max(len(tid) for tid in target_ids)
    for length in range(MIN_TARGET_PREFIX_LEN, max_len + 1):
        prefixes = {tid[:length].upper() for tid in target_ids}
        if len(prefixes) == len(target_ids):
            return length
    return max_len
