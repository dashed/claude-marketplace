import sys
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# ---------------------------------------------------------------------------
# Marketplace plugin packaging shim
# ---------------------------------------------------------------------------
# Upstream (mcp-personal) keeps mcp_fd_server.py at the repo root, so the test
# suite launches it by the BARE name "mcp_fd_server.py" (see test_cli.py and the
# `cli_client` fixture below). In this plugin layout the script lives one level
# down under ../scripts/, so that bare name no longer resolves from the test
# working directory.
#
# Rather than editing the upstream test bodies, this autouse fixture chdirs into
# the scripts/ directory for the duration of every test, so the relative name
# "mcp_fd_server.py" resolves to the real server. (Import-based tests resolve via
# pythonpath = ["scripts"] in pyproject.toml instead.) monkeypatch.chdir is
# automatically reverted after each test. Files the tests operate on are created
# under pytest's absolute `tmp_path`, so the changed cwd does not affect them.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture(autouse=True)
def _chdir_to_scripts(monkeypatch):
    monkeypatch.chdir(SCRIPTS_DIR)


@pytest.fixture
async def cli_client():
    """
    Optional fixture for testing the packaged script end-to-end.
    This runs the script as a subprocess with stdio transport.
    """
    server_params = StdioServerParameters(
        command=sys.executable, args=["mcp_fd_server.py"]
    )

    async with stdio_client(server_params) as streams:
        read_stream, write_stream = streams
        client_session = ClientSession(read_stream, write_stream)
        await client_session.initialize()
        yield client_session
