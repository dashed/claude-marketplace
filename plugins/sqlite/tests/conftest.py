"""Test configuration for the bundled SQLite MCP server.

The upstream suite was written to run from the repository root where the
server script sits beside the tests. In this plugin the server lives under
``scripts/`` instead, so two location assumptions need bridging:

1. ``import mcp_sqlite_server`` — handled by ``pythonpath = ["scripts"]`` in
   pyproject.toml; we also insert it on ``sys.path`` here as a safety net.
2. ``run_cli_command`` subprocesses the server by bare filename
   (``mcp_sqlite_server.py``), which only resolves when the CWD is the script
   directory. We resolve its absolute path and expose it as ``SERVER_SCRIPT``
   so the test's subprocess call locates it regardless of the working
   directory. This is the only change to the upstream test logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
SERVER_SCRIPT = str(SCRIPTS_DIR / "mcp_sqlite_server.py")

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
