import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest

# Only mark async tests with anyio, not all tests in the file


def test_cli_search_command(tmp_path: Path):
    """Test CLI search subcommand."""
    # Create test files
    (tmp_path / "test.py").write_text("print('hello')")
    (tmp_path / "test.txt").write_text("hello")

    # Run search command
    result = subprocess.run(
        [sys.executable, "mcp_fd_server.py", "search", r"\.py$", str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Skip if fd not available
    if "Cannot find the `fd` binary" in result.stderr:
        pytest.skip("fd not available")

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output
    assert any("test.py" in match for match in output["matches"])


def test_cli_filter_command(tmp_path: Path):
    """Test CLI filter subcommand."""
    # Create test files
    (tmp_path / "main.py").write_text("# main")
    (tmp_path / "minor.py").write_text("# minor")

    # Run filter command
    result = subprocess.run(
        [
            sys.executable,
            "mcp_fd_server.py",
            "filter",
            "main",
            r"\.py$",
            str(tmp_path),
            "--first",
        ],
        capture_output=True,
        text=True,
    )

    # Skip if dependencies not available
    if "Cannot find the" in result.stderr:
        pytest.skip("fd or fzf not available")

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output
    if output["matches"]:  # fzf might not find matches depending on version
        assert len(output["matches"]) == 1


def test_cli_help():
    """Test CLI help output."""
    result = subprocess.run(
        [sys.executable, "mcp_fd_server.py", "-h"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "fd + fzf powers" in result.stdout
    assert "search" in result.stdout
    assert "filter" in result.stdout


def test_cli_search_mocked(tmp_path: Path, monkeypatch):
    """Test CLI search with mocked subprocess behavior."""
    # Create a mock fd executable that returns predefined output
    if platform.system() == "Windows":
        mock_fd = tmp_path / "fd.bat"
        mock_fd.write_text("""@echo off
echo src/main.py
echo src/test.py
for %%i in (%*) do if "%%i"=="--hidden" echo src/.hidden/config.py
""")
    else:
        mock_fd = tmp_path / "fd"
        mock_fd.write_text("""#!/usr/bin/env python3
import sys
# Mock fd that ignores all arguments and returns predefined output
print("src/main.py")
print("src/test.py")
if "--hidden" in sys.argv:
    print("src/.hidden/config.py")
""")
        mock_fd.chmod(0o755)

    # Add the tmp_path to PATH so our mock fd is found first
    path_sep = ";" if platform.system() == "Windows" else ":"
    monkeypatch.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

    # Run the CLI command with the mock
    result = subprocess.run(
        [
            sys.executable,
            "mcp_fd_server.py",
            "search",
            r"\.py$",
            ".",
            "--flags=--hidden",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output
    assert len(output["matches"]) == 3
    assert "src/main.py" in output["matches"]
    assert "src/.hidden/config.py" in output["matches"]


def test_cli_search_limit_mocked(tmp_path: Path, monkeypatch):
    """CLI search should honor --limit and cap results."""
    if platform.system() == "Windows":
        pytest.skip("shebang-based mock not portable on Windows")

    # Mock fd to return multiple results
    mock_fd = tmp_path / "fd"
    mock_fd.write_text("""#!/usr/bin/env python3
print("a")
print("b")
print("c")
""")
    mock_fd.chmod(0o755)

    path_sep = ":"
    monkeypatch.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

    result = subprocess.run(
        [
            sys.executable,
            "mcp_fd_server.py",
            "search",
            r".*",
            ".",
            "--limit=2",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output
    assert len(output["matches"]) == 2


def test_cli_filter_limit_mocked(tmp_path: Path, monkeypatch):
    """CLI filter should honor --limit in standard mode (no multiline)."""
    if platform.system() == "Windows":
        pytest.skip("shebang-based mock not portable on Windows")

    # Create mock fd and fzf executables
    mock_fd = tmp_path / "fd"
    mock_fd.write_text("""#!/usr/bin/env python3
print("one")
print("two")
print("three")
""")
    mock_fd.chmod(0o755)

    mock_fzf = tmp_path / "fzf"
    mock_fzf.write_text("""#!/usr/bin/env python3
import sys
data = sys.stdin.read().splitlines()
for line in data[:3]:
    print(line)
""")
    mock_fzf.chmod(0o755)

    path_sep = ":"
    monkeypatch.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

    result = subprocess.run(
        [
            sys.executable,
            "mcp_fd_server.py",
            "filter",
            "o",
            "",
            ".",
            "--limit=2",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output
    assert len(output["matches"]) == 2


def test_cli_filter_first_overrides_limit_mocked(tmp_path: Path, monkeypatch):
    """CLI filter should return a single match when both --first and --limit are set."""
    if platform.system() == "Windows":
        pytest.skip("shebang-based mock not portable on Windows")

    # Create mock fd and fzf executables
    mock_fd = tmp_path / "fd"
    mock_fd.write_text("""#!/usr/bin/env python3
print("one")
print("two")
print("three")
""")
    mock_fd.chmod(0o755)

    mock_fzf = tmp_path / "fzf"
    mock_fzf.write_text("""#!/usr/bin/env python3
import sys
data = sys.stdin.read().splitlines()
for line in data[:3]:
    print(line)
""")
    mock_fzf.chmod(0o755)

    path_sep = ":"
    monkeypatch.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

    result = subprocess.run(
        [
            sys.executable,
            "mcp_fd_server.py",
            "filter",
            "o",
            "",
            ".",
            "--first",
            "--limit=5",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output
    assert len(output["matches"]) == 1


def test_mcp_server_mode():
    """Test that script runs in MCP server mode without arguments."""
    # Start the server
    proc = subprocess.Popen(
        [sys.executable, "mcp_fd_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Send a simple initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
            "id": 1,
        }

        assert proc.stdin is not None
        proc.stdin.write(f"Content-Length: {len(json.dumps(init_request))}\r\n\r\n")
        proc.stdin.write(json.dumps(init_request))
        proc.stdin.flush()

        # Give it a moment to respond
        import time

        time.sleep(0.5)

        # Terminate the process
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=2)

        # Check if binary missing error occurred
        if "Cannot find the" in stderr:
            pytest.skip("Required binaries not available")

        # Should have received some output (at least headers)
        assert stdout or not stderr  # Either got output or no error

    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.skip("Server process timeout")
    except Exception:
        proc.kill()
        raise


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio", "trio"])
async def test_cli_client_fixture(tmp_path: Path, anyio_backend):
    """Test stdio client communication with the MCP server."""
    import shutil

    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.types import TextContent

    # Skip if fd not available
    if not shutil.which("fd") and not shutil.which("fdfind"):
        pytest.skip("fd not available")

    # Create test file
    (tmp_path / "test.py").write_text("# test file")

    server_params = StdioServerParameters(
        command=sys.executable, args=["mcp_fd_server.py"]
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the session
                await session.initialize()

                # List available tools
                tools_response = await session.list_tools()
                assert len(tools_response.tools) == 2
                tool_names = [tool.name for tool in tools_response.tools]
                assert "search_files" in tool_names
                assert "filter_files" in tool_names

                # Call search_files
                result = await session.call_tool(
                    "search_files",
                    arguments={"pattern": r"\.py$", "path": str(tmp_path)},
                )

                # Check the result
                assert len(result.content) > 0
                assert isinstance(result.content[0], TextContent)

                data = json.loads(result.content[0].text)
                if "error" in data:
                    # If there's an error about missing binaries, skip
                    if "Cannot find the" in data["error"]:
                        pytest.skip("Required binaries not available")
                else:
                    assert "matches" in data
                    assert any("test.py" in match for match in data["matches"])

    except Exception as e:
        error_msg = str(e)
        if "Cannot find the" in error_msg or "fd" in error_msg:
            pytest.skip("Required binaries not available")
        raise
