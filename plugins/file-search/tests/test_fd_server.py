import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

import mcp_fd_server


def normalize_path(path):
    """Normalize path to use forward slashes for cross-platform testing."""
    # Use pathlib for proper path handling
    return Path(path).as_posix()


pytestmark = pytest.mark.anyio


def _skip_if_missing(binary: str):
    """Skip test if binary is not available on PATH."""
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not on PATH")


async def test_search_files_finds_python(tmp_path: Path):
    """Test that search_files correctly finds Python files."""
    _skip_if_missing("fd")

    # Arrange
    (tmp_path / "one.py").write_text("print('hi')")
    (tmp_path / "two.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "three.py").write_text("# python file")

    # Act
    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool(
            "search_files", {"pattern": r"\.py$", "path": str(tmp_path)}
        )

        # Assert
        assert hasattr(result, "content")
        assert len(result.content) > 0
        content = result.content[0]
        assert content.type == "text"

        data = json.loads(content.text)
        assert "matches" in data
        assert normalize_path(tmp_path / "one.py") in data["matches"]
        assert normalize_path(tmp_path / "subdir" / "three.py") in data["matches"]
        assert all(p.endswith(".py") for p in data["matches"])
        assert normalize_path(tmp_path / "two.txt") not in data["matches"]


async def test_search_files_with_flags(tmp_path: Path):
    """Test search_files with additional fd flags."""
    _skip_if_missing("fd")

    # Arrange
    (tmp_path / ".hidden.py").write_text("# hidden")
    (tmp_path / "visible.py").write_text("# visible")

    # Act without hidden flag

    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result_no_hidden = await client.call_tool(
            "search_files", {"pattern": r"\.py$", "path": str(tmp_path)}
        )
        data_no_hidden = json.loads(result_no_hidden.content[0].text)

        # Act with hidden flag
        result_with_hidden = await client.call_tool(
            "search_files",
            {"pattern": r"\.py$", "path": str(tmp_path), "flags": "--hidden"},
        )
        data_with_hidden = json.loads(result_with_hidden.content[0].text)

        # Assert
        assert normalize_path(tmp_path / "visible.py") in data_no_hidden["matches"]
        assert normalize_path(tmp_path / ".hidden.py") not in data_no_hidden["matches"]
        assert normalize_path(tmp_path / ".hidden.py") in data_with_hidden["matches"]


async def test_search_files_error_handling():
    """Test search_files error handling for missing pattern."""
    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool("search_files", {"pattern": ""})

        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "'pattern' argument is required" in data["error"]


async def test_filter_files_returns_best_match(tmp_path: Path):
    """Test filter_files with fuzzy matching."""
    _skip_if_missing("fd")
    _skip_if_missing("fzf")

    # Arrange
    (tmp_path / "main.rs").write_text("// rust")
    (tmp_path / "minor.rs").write_text("// rust")
    (tmp_path / "maintenance.rs").write_text("// rust")

    # Act
    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool(
            "filter_files",
            {
                "filter": "main",
                "pattern": r"\.rs$",
                "path": str(tmp_path),
                "first": True,
            },
        )

        # Assert
        data = json.loads(result.content[0].text)
        assert "matches" in data
        assert len(data["matches"]) == 1
        assert data["matches"][0] == normalize_path(tmp_path / "main.rs")


async def test_filter_files_multiple_matches(tmp_path: Path):
    """Test filter_files returning multiple fuzzy matches."""
    _skip_if_missing("fd")
    _skip_if_missing("fzf")

    # Arrange
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "configuration.yaml").write_text("key: value")
    (tmp_path / "settings.toml").write_text("[section]")

    # Act
    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool(
            "filter_files", {"filter": "conf", "path": str(tmp_path)}
        )

        # Assert
        data = json.loads(result.content[0].text)
        assert "matches" in data
        assert any("config" in p for p in data["matches"])


async def test_filter_files_error_handling():
    """Test filter_files error handling for missing filter."""
    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool("filter_files", {"filter": ""})

        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "'filter' argument is required" in data["error"]


async def test_list_tools():
    """Test that tools are properly exposed with correct metadata."""
    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.list_tools()

        # Should have exactly 2 tools
        assert len(result.tools) == 2

        # Find tools by name
        search_tool = next(t for t in result.tools if t.name == "search_files")
        filter_tool = next(t for t in result.tools if t.name == "filter_files")

        # Verify search_files metadata
        assert search_tool.description.startswith(
            "Search for files using patterns (powered by fd"
        )
        assert "pattern" in search_tool.inputSchema["required"]

        # Verify filter_files metadata
        assert filter_tool.description.startswith(
            "Fuzzy search for files by NAME using fzf"
        )
        assert "filter" in filter_tool.inputSchema["required"]


def test_binary_discovery():
    """Test binary discovery logic for fd and fzf."""
    with patch("shutil.which") as mock_which:
        # Test fd discovery (fd takes precedence over fdfind)
        mock_which.side_effect = lambda x: (
            "/usr/bin/fd"
            if x == "fd"
            else ("/usr/bin/fdfind" if x == "fdfind" else None)
        )
        fd_path = mock_which("fd") or mock_which("fdfind")
        assert fd_path == "/usr/bin/fd"

        # Test fdfind fallback (Debian/Ubuntu)
        mock_which.side_effect = lambda x: "/usr/bin/fdfind" if x == "fdfind" else None
        fd_path = mock_which("fd") or mock_which("fdfind")
        assert fd_path == "/usr/bin/fdfind"

        # Reset side_effect and test no fd available
        mock_which.side_effect = None
        mock_which.return_value = None
        fd_path = mock_which("fd") or mock_which("fdfind")
        assert fd_path is None


def test_require_binary():
    """Test the _require helper function."""
    # Valid binary
    assert mcp_fd_server._require("/usr/bin/fd", "fd") == "/usr/bin/fd"

    # Missing binary
    with pytest.raises(mcp_fd_server.BinaryMissing) as exc_info:
        mcp_fd_server._require(None, "fd")

    assert "Cannot find the `fd` binary" in str(exc_info.value)


@patch("subprocess.check_output")
async def test_search_files_mocked(mock_check_output):
    """Test search_files with mocked subprocess for CI environments."""
    # Mock fd output
    mock_check_output.return_value = "src/main.py\nsrc/test.py\n"

    # Override binary check
    import json

    with patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"):
        async with client_session(mcp_fd_server.mcp._mcp_server) as client:
            result = await client.call_tool(
                "search_files", {"pattern": r"\.py$", "path": "src"}
            )

            # Assert
            data = json.loads(result.content[0].text)
            assert data["matches"] == ["src/main.py", "src/test.py"]
            mock_check_output.assert_called_once()


@patch("subprocess.Popen")
@patch("subprocess.check_output")
async def test_filter_files_mocked(mock_check_output, mock_popen):
    """Test filter_files with mocked subprocess for CI environments."""
    # Mock fd process
    fd_proc = MagicMock()
    fd_proc.stdout = MagicMock()
    mock_popen.return_value = fd_proc

    # Mock fzf output
    mock_check_output.return_value = "src/main.py\n"

    # Override binary checks
    with (
        patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"),
        patch.object(mcp_fd_server, "FZF_EXECUTABLE", "/mock/fzf"),
    ):
        async with client_session(mcp_fd_server.mcp._mcp_server) as client:
            result = await client.call_tool(
                "filter_files", {"filter": "main", "pattern": r"\.py$"}
            )

            # Assert
            data = json.loads(result.content[0].text)
            assert data["matches"] == ["src/main.py"]


# Additional comprehensive tests


async def test_search_files_default_path():
    """Test search_files with default path (current directory)."""
    _skip_if_missing("fd")

    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool("search_files", {"pattern": r"\.py$"})

        data = json.loads(result.content[0].text)
        # Should find some .py files in current directory (at least mcp_fd_server.py)
        assert "matches" in data


async def test_filter_files_with_fd_and_fzf_flags(tmp_path: Path):
    """Test filter_files with additional fd and fzf flags."""
    _skip_if_missing("fd")
    _skip_if_missing("fzf")

    # Create test files
    (tmp_path / ".env.local").write_text("SECRET=hidden")
    (tmp_path / "config.env").write_text("PUBLIC=visible")

    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool(
            "filter_files",
            {
                "filter": "env",
                "pattern": "env",
                "path": str(tmp_path),
                "fd_flags": "--hidden",
                "fzf_flags": "--exact",
            },
        )

        data = json.loads(result.content[0].text)
        assert "matches" in data
        # Should find both files with --hidden flag
        assert len(data["matches"]) >= 1


async def test_search_files_with_multiple_flags(tmp_path: Path):
    """Test search_files with multiple fd flags."""
    _skip_if_missing("fd")

    # Create test structure
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "secret.py").write_text("# secret")
    (tmp_path / "public.py").write_text("# public")

    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool(
            "search_files",
            {"pattern": r"\.py$", "path": str(tmp_path), "flags": "--hidden --type f"},
        )

        data = json.loads(result.content[0].text)
        assert "matches" in data
        # Should find both files with --hidden flag
        assert any("secret.py" in match for match in data["matches"])
        assert any("public.py" in match for match in data["matches"])


async def test_empty_search_results(tmp_path: Path):
    """Test behavior when search returns no results."""
    _skip_if_missing("fd")

    # Create directory with no matching files
    (tmp_path / "readme.txt").write_text("documentation")

    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool(
            "search_files", {"pattern": r"\.nonexistent$", "path": str(tmp_path)}
        )

        data = json.loads(result.content[0].text)
        assert "matches" in data
        assert data["matches"] == []


async def test_filter_files_empty_results(tmp_path: Path):
    """Test filter_files with no fuzzy matches."""
    _skip_if_missing("fd")
    _skip_if_missing("fzf")

    # Create test files
    (tmp_path / "alpha.txt").write_text("content")
    (tmp_path / "beta.txt").write_text("content")

    async with client_session(mcp_fd_server.mcp._mcp_server) as client:
        result = await client.call_tool(
            "filter_files",
            {"filter": "zzz_nonmatch", "pattern": r"\.txt$", "path": str(tmp_path)},
        )

        data = json.loads(result.content[0].text)
        # fzf may return error for no matches, or empty matches list
        if "error" in data:
            # This is acceptable - fzf can return error when no matches
            assert isinstance(data["error"], str)
        else:
            assert "matches" in data
            assert isinstance(data["matches"], list)


# CLI interface tests


def test_cli_search_command(tmp_path: Path):
    """Test CLI search subcommand."""
    # Create test files
    (tmp_path / "test.py").write_text("print('hello')")
    (tmp_path / "test.txt").write_text("hello")

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


def test_cli_with_flags(tmp_path: Path):
    """Test CLI with additional flags."""
    # Create test files including hidden
    (tmp_path / "visible.py").write_text("# visible")
    (tmp_path / ".hidden.py").write_text("# hidden")

    result = subprocess.run(
        [
            sys.executable,
            "mcp_fd_server.py",
            "search",
            r"\.py$",
            str(tmp_path),
            "--flags=--hidden",  # Use equals syntax for flags
        ],
        capture_output=True,
        text=True,
    )

    if "Cannot find the `fd` binary" in result.stderr:
        pytest.skip("fd not available")

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output
    # Should find both visible and hidden files
    matches = output["matches"]
    assert any("visible.py" in match for match in matches)
    assert any(".hidden.py" in match for match in matches)


# Additional mock-based tests that don't require real binaries

monkeypatch = pytest.MonkeyPatch()


def test_fd_flag_handling(tmp_path: Path):
    """Test that fzf exit code FZF_EXIT_NO_MATCH (1) returns empty matches, not error."""
    if platform.system() == "Windows":
        mock_fd = tmp_path / "fd.bat"
        mock_fd.write_text("""@echo off
echo file1.txt
echo file2.log
""")

        mock_fzf = tmp_path / "fzf.bat"
        mock_fzf.write_text(f"""@echo off
rem fzf returns exit code {mcp_fd_server.FZF_EXIT_NO_MATCH} when no matches found
exit /b {mcp_fd_server.FZF_EXIT_NO_MATCH}
""")
    else:
        mock_fd = tmp_path / "fd"
        mock_fd.write_text("""#!/usr/bin/env python3
import sys
print("file1.txt")
print("file2.log")
sys.exit(0)
""")
        mock_fd.chmod(0o755)

        mock_fzf = tmp_path / "fzf"
        mock_fzf.write_text(f"""#!/usr/bin/env python3
import sys
# fzf returns exit code {mcp_fd_server.FZF_EXIT_NO_MATCH} when no matches found
sys.exit({mcp_fd_server.FZF_EXIT_NO_MATCH})
""")
        mock_fzf.chmod(0o755)

    with monkeypatch.context() as m:
        path_sep = ";" if platform.system() == "Windows" else ":"
        m.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

        # Reload module globals to pick up new executables
        mcp_fd_server.FD_EXECUTABLE = shutil.which("fd") or shutil.which("fdfind")
        mcp_fd_server.FZF_EXECUTABLE = shutil.which("fzf")

        result = mcp_fd_server.filter_files("nomatch")

        # Should handle empty results gracefully (FZF_EXIT_NO_MATCH = no matches, not error)
        assert "matches" in result
        assert result["matches"] == []


def test_fzf_actual_error_handling(tmp_path: Path):
    """Test that fzf exit code FZF_EXIT_ERROR (2) is properly reported as an error."""
    if platform.system() == "Windows":
        mock_fd = tmp_path / "fd.bat"
        mock_fd.write_text("""@echo off
echo file1.txt
echo file2.log
""")

        mock_fzf = tmp_path / "fzf.bat"
        mock_fzf.write_text(f"""@echo off
rem fzf returns exit code {mcp_fd_server.FZF_EXIT_ERROR} for actual errors
echo Error: fzf encountered an error >&2
exit /b {mcp_fd_server.FZF_EXIT_ERROR}
""")
    else:
        mock_fd = tmp_path / "fd"
        mock_fd.write_text("""#!/usr/bin/env python3
import sys
print("file1.txt")
print("file2.log")
sys.exit(0)
""")
        mock_fd.chmod(0o755)

        mock_fzf = tmp_path / "fzf"
        mock_fzf.write_text(f"""#!/usr/bin/env python3
import sys
# fzf returns exit code {mcp_fd_server.FZF_EXIT_ERROR} for actual errors
print("Error: fzf encountered an error", file=sys.stderr)
sys.exit({mcp_fd_server.FZF_EXIT_ERROR})
""")
        mock_fzf.chmod(0o755)

    with monkeypatch.context() as m:
        path_sep = ";" if platform.system() == "Windows" else ":"
        m.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

        # Reload module globals to pick up new executables
        mcp_fd_server.FD_EXECUTABLE = shutil.which("fd") or shutil.which("fdfind")
        mcp_fd_server.FZF_EXECUTABLE = shutil.which("fzf")

        result = mcp_fd_server.filter_files("searchterm")

        # Should return an error for FZF_EXIT_ERROR, not empty matches
        assert "error" in result
        assert "matches" not in result
        # The error should contain information about the subprocess error
        assert (
            "CalledProcessError" in result["error"] or "exit" in result["error"].lower()
        )


def test_fzf_actual_error_handling_multiline(tmp_path: Path):
    """Test that fzf exit code FZF_EXIT_ERROR (2) in multiline mode is properly reported as an error."""
    # Create test files with content
    test_file1 = tmp_path / "test1.txt"
    test_file1.write_text("content1")
    test_file2 = tmp_path / "test2.txt"
    test_file2.write_text("content2")

    if platform.system() == "Windows":
        mock_fd = tmp_path / "fd.bat"
        mock_fd.write_text(f"""@echo off
echo {test_file1}
echo {test_file2}
""")

        mock_fzf = tmp_path / "fzf.bat"
        mock_fzf.write_text(f"""@echo off
rem fzf returns exit code {mcp_fd_server.FZF_EXIT_ERROR} for actual errors in multiline mode
echo Error: fzf multiline processing failed >&2
exit /b {mcp_fd_server.FZF_EXIT_ERROR}
""")
    else:
        mock_fd = tmp_path / "fd"
        mock_fd.write_text(f"""#!/usr/bin/env python3
import sys
print("{test_file1}")
print("{test_file2}")
sys.exit(0)
""")
        mock_fd.chmod(0o755)

        mock_fzf = tmp_path / "fzf"
        mock_fzf.write_text(f"""#!/usr/bin/env python3
import sys
# fzf returns exit code {mcp_fd_server.FZF_EXIT_ERROR} for actual errors in multiline mode
print("Error: fzf multiline processing failed", file=sys.stderr)
sys.exit({mcp_fd_server.FZF_EXIT_ERROR})
""")
        mock_fzf.chmod(0o755)

    with monkeypatch.context() as m:
        path_sep = ";" if platform.system() == "Windows" else ":"
        m.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

        # Reload module globals to pick up new executables
        mcp_fd_server.FD_EXECUTABLE = shutil.which("fd") or shutil.which("fdfind")
        mcp_fd_server.FZF_EXECUTABLE = shutil.which("fzf")

        result = mcp_fd_server.filter_files("searchterm", multiline=True)

        # Should return an error for FZF_EXIT_ERROR in multiline mode too
        assert "error" in result
        assert "matches" not in result
        # The error should contain information about the subprocess error
        assert (
            "CalledProcessError" in result["error"] or "exit" in result["error"].lower()
        )


def test_multiline_support(tmp_path: Path):
    """Test multiline support in filter_files."""
    # Create test files with content
    test_file1 = tmp_path / "test1.txt"
    test_file1.write_text("line 1\nline 2\nfunction foo() {\n  return bar;\n}")

    test_file2 = tmp_path / "test2.py"
    test_file2.write_text("import os\ndef main():\n    print('hello')")

    if platform.system() == "Windows":
        mock_fd = tmp_path / "fd.bat"
        mock_fd.write_text(f"""@echo off
echo {test_file1}
echo {test_file2}
""")

        mock_fzf = tmp_path / "fzf.bat"
        # Create a Python script that fzf.bat will call
        fzf_py = tmp_path / "fzf_impl.py"
        # Escape the path for use in Python string
        escaped_path = str(test_file1).replace("\\", "\\\\")
        fzf_py.write_text(f'''import sys
if "--read0" in sys.argv and "--print0" in sys.argv:
    # Read null-delimited input
    data = sys.stdin.buffer.read()
    # Look for "function" in the content
    if b"function" in data:
        # Return matching file record with null terminator
        content = "{escaped_path}:\\nline 1\\nline 2\\nfunction foo() {{\\n  return bar;\\n}}"
        print(content, end="\\0")
''')
        mock_fzf.write_text(f'@echo off\n{sys.executable} "{fzf_py}" %*')
    else:
        mock_fd = tmp_path / "fd"
        mock_fd.write_text(f'''#!/usr/bin/env python3
import sys
print("{test_file1}")
print("{test_file2}")
''')
        mock_fd.chmod(0o755)

        mock_fzf = tmp_path / "fzf"
        mock_fzf.write_text(f'''#!/usr/bin/env python3
import sys
if "--read0" in sys.argv and "--print0" in sys.argv:
    # Read null-delimited input
    data = sys.stdin.buffer.read()
    # Look for "function" in the content
    if b"function" in data:
        # Return matching file record with null terminator
        content = "{test_file1}:\\nline 1\\nline 2\\nfunction foo() {{\\n  return bar;\\n}}"
        print(content, end="\\0")
''')
        mock_fzf.chmod(0o755)

    with monkeypatch.context() as m:
        path_sep = ";" if platform.system() == "Windows" else ":"
        m.setenv("PATH", f"{tmp_path}{path_sep}{os.environ.get('PATH', '')}")

        # Reload module globals to pick up new executables
        mcp_fd_server.FD_EXECUTABLE = shutil.which("fd") or shutil.which("fdfind")
        mcp_fd_server.FZF_EXECUTABLE = shutil.which("fzf")

        result = mcp_fd_server.filter_files("function", multiline=True)

        assert "matches" in result
        matches = result["matches"]
        assert len(matches) > 0
        assert "function foo()" in matches[0]


def test_multiline_cli_support():
    """Test CLI support for multiline flag."""
    with patch("mcp_fd_server.filter_files") as mock_filter:
        mock_filter.return_value = {"matches": ["file1.txt"]}

        with patch(
            "sys.argv", ["mcp_fd_server.py", "filter", "test", "", ".", "--multiline"]
        ):
            mcp_fd_server._cli()

        # Verify multiline=True was passed as a positional argument
        mock_filter.assert_called_once()
        call_args = mock_filter.call_args
        # The function signature is filter_files(filter, pattern, path, first, limit, fd_flags, fzf_flags, multiline)
        # So multiline should be the 8th argument (index 7)
        if len(call_args[0]) > 7:
            assert call_args[0][7] is True  # positional argument
        else:
            # Check if it was passed as keyword argument
            assert call_args[1].get("multiline") is True


async def test_filter_files_multiline_mcp():
    """Test multiline support through MCP interface."""
    test_content = "function example() {\n  return 'hello';\n}"

    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = (
            test_content.encode()
        )

        with (
            patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"),
            patch.object(mcp_fd_server, "FZF_EXECUTABLE", "/mock/fzf"),
            patch("subprocess.check_output") as mock_fd_output,
            patch("subprocess.Popen") as mock_popen,
        ):
            # Mock fd listing files
            mock_fd_output.return_value = "test.js\n"

            # Mock fzf finding the function
            mock_fzf_proc = MagicMock()
            mock_fzf_proc.communicate.return_value = (
                b"test.js:\nfunction example() {\n  return 'hello';\n}\x00",
                b"",
            )
            mock_fzf_proc.returncode = 0  # Success
            mock_popen.return_value = mock_fzf_proc

            async with client_session(mcp_fd_server.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "filter_files", {"filter": "function", "multiline": True}
                )

                data = json.loads(result.content[0].text)
                assert "matches" in data
                assert len(data["matches"]) > 0
                assert "function example()" in data["matches"][0]


def test_windows_path_normalization():
    """Test that Windows paths are properly normalized to forward slashes."""
    # Test various Windows path formats
    test_cases = [
        (r"C:\Users\test\file.py", "C:/Users/test/file.py"),
        (r"D:\Projects\my-app\src\main.py", "D:/Projects/my-app/src/main.py"),
        (r"\\network\share\file.txt", "//network/share/file.txt"),
        (r"C:" + "\\", "C:/"),
        (r"relative\path\file.py", "relative/path/file.py"),
    ]

    for windows_path, expected in test_cases:
        result = mcp_fd_server._normalize_path(windows_path)
        assert result == expected, f"Failed to normalize {windows_path}"


def test_search_files_windows_path_output():
    """Test that search_files normalizes Windows paths in subprocess output."""
    with patch("subprocess.check_output") as mock_check_output:
        # Mock fd returning Windows-style paths
        mock_check_output.return_value = (
            r"C:\Users\test\file1.py"
            + "\n"
            + r"D:\Projects\app\main.py"
            + "\n"
            + r"\\network\share\script.py"
            + "\n"
        )

        with patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"):
            result = mcp_fd_server.search_files("*.py", ".")

            assert "matches" in result
            assert len(result["matches"]) == 3

            # All paths should be normalized to forward slashes
            assert result["matches"][0] == "C:/Users/test/file1.py"
            assert result["matches"][1] == "D:/Projects/app/main.py"
            assert result["matches"][2] == "//network/share/script.py"

            # No backslashes should remain
    for match in result["matches"]:
        assert "\\" not in match


def test_filter_files_first_overrides_limit_standard_mode():
    """first=True should override limit and return exactly one match in standard mode."""

    class _MockPopen:
        def __init__(self, *args, **kwargs):
            self.stdout = None

        def wait(self):
            return 0

    def fake_check_output(cmd, *args, **kwargs):  # fzf output or fd list
        # If command looks like fzf (contains '--filter'), return multiple matches
        if isinstance(cmd, list) and "--filter" in cmd:
            return "alpha\nbeta\ngamma\n"
        # Else return dummy fd listing
        return "alpha\nbeta\ngamma\n"

    with (
        patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"),
        patch.object(mcp_fd_server, "FZF_EXECUTABLE", "/mock/fzf"),
        patch("subprocess.Popen", side_effect=_MockPopen),
        patch("subprocess.check_output", side_effect=fake_check_output),
    ):
        res = mcp_fd_server.filter_files("a", pattern="", path=".", first=True, limit=5)
        assert "matches" in res
        assert len(res["matches"]) == 1


def test_filter_files_limit_trims_results_multiline_mode(tmp_path):
    """In multiline mode, limit should trim results when first is not set."""
    # Prepare a couple of files and contents
    files = []
    for i, content in enumerate(
        [b"function a(){}", b"function b(){}", b"function c(){}"], start=1
    ):
        p = tmp_path / f"f{i}.js"
        p.write_bytes(content)
        files.append(str(p))

    # Mock fd to list our files, and fzf to pass them through when filtering 'function'
    def fake_fd_output(cmd, *args, **kwargs):
        return "\n".join(files) + "\n"

    class _MockFzfProc:
        def __init__(self, *args, **kwargs):
            self._out = b"".join(
                [
                    f"{mcp_fd_server._normalize_path(f)}:\n".encode()
                    + open(f, "rb").read()
                    + b"\0"
                    for f in files
                ]
            )
            self.returncode = 0  # Success

        def communicate(self, data):
            # Pretend fzf returned all entries (already contains NULs)
            return self._out, b""

    with (
        patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"),
        patch.object(mcp_fd_server, "FZF_EXECUTABLE", "/mock/fzf"),
        patch("subprocess.check_output", side_effect=fake_fd_output),
        patch("subprocess.Popen", side_effect=_MockFzfProc),
    ):
        res = mcp_fd_server.filter_files("function", multiline=True, limit=2)
        assert "matches" in res
        assert len(res["matches"]) == 2


def test_search_files_limit_uses_fd_max_results_and_trims():
    """search_files should add '-n <limit>' to fd and trim results as a safety."""
    captured_cmds = []

    def fake_check_output(cmd, *args, **kwargs):  # type: ignore[no-redef]
        # Record the command to inspect flags
        captured_cmds.append(cmd if isinstance(cmd, list) else [cmd])
        # Always return 3 lines
        return "a\nB\nc\n"

    with (
        patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"),
        patch("subprocess.check_output", side_effect=fake_check_output),
    ):
        # With limit=2, ensure '--max-results 2' is present and result trimmed to 2
        res = mcp_fd_server.search_files(".*", ".", limit=2)
        assert "matches" in res
        assert len(res["matches"]) == 2
        # Verify the first recorded cmd includes --max-results 2
        assert any(
            isinstance(cmd, list) and "--max-results" in cmd and str(2) in cmd
            for cmd in captured_cmds
        )

    # No limit should not include -n
    captured_cmds.clear()
    with (
        patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"),
        patch("subprocess.check_output", side_effect=fake_check_output),
    ):
        res = mcp_fd_server.search_files(".*", ".", limit=0)
        assert "matches" in res
        assert len(res["matches"]) == 3
        assert all(
            "--max-results" not in (cmd if isinstance(cmd, list) else [cmd])
            for cmd in captured_cmds
        )


def test_filter_files_limit_trims_results_standard_mode():
    """filter_files should trim to 'limit' when not using 'first' (standard mode)."""

    class _MockPopen:
        def __init__(self, *args, **kwargs):
            self.stdout = None

        def wait(self):
            return 0

    def fake_check_output(cmd, *args, **kwargs):  # fzf output or fd list
        # If command looks like fzf (contains '--filter'), return three matches
        if isinstance(cmd, list) and "--filter" in cmd:
            return "x\ny\nz\n"
        # Else return dummy fd listing
        return "x\ny\nz\n"

    with (
        patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"),
        patch.object(mcp_fd_server, "FZF_EXECUTABLE", "/mock/fzf"),
        patch("subprocess.Popen", side_effect=_MockPopen),
        patch("subprocess.check_output", side_effect=fake_check_output),
    ):
        res = mcp_fd_server.filter_files(
            "term", pattern="", path=".", first=False, limit=2
        )
        assert "matches" in res
        assert len(res["matches"]) == 2
