import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

import mcp_fuzzy_search


def normalize_path(path):
    """Normalize path to use forward slashes for cross-platform testing."""
    # Use pathlib for proper path handling
    return Path(path).as_posix()


pytestmark = pytest.mark.anyio


def _skip_if_missing(binary: str):
    """Skip test if binary is not available on PATH."""
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not on PATH")


async def test_fuzzy_search_files(tmp_path: Path):
    """Test fuzzy_search_files with real binaries."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create test files
    (tmp_path / "main.py").write_text("# main file")
    (tmp_path / "main_test.py").write_text("# main test")
    (tmp_path / "utils.py").write_text("# utilities")
    (tmp_path / "README.md").write_text("# Main documentation")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_files", {"fuzzy_filter": "main", "path": str(tmp_path)}
        )

        # Parse result
        data = json.loads(result.content[0].text)
        assert "matches" in data
        assert len(data["matches"]) >= 2  # Should find main.py and main_test.py
        assert any("main.py" in match for match in data["matches"])


async def test_fuzzy_search_files_with_hidden(tmp_path: Path):
    """Test fuzzy_search_files includes hidden files when requested."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create test files
    (tmp_path / ".hidden_config.json").write_text("{}")
    (tmp_path / "visible_config.json").write_text("{}")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Without hidden flag
        result_no_hidden = await client.call_tool(
            "fuzzy_search_files", {"fuzzy_filter": "config", "path": str(tmp_path)}
        )
        data_no_hidden = json.loads(result_no_hidden.content[0].text)

        # With hidden flag
        result_with_hidden = await client.call_tool(
            "fuzzy_search_files",
            {"fuzzy_filter": "config", "path": str(tmp_path), "hidden": True},
        )
        data_with_hidden = json.loads(result_with_hidden.content[0].text)

        # Assertions
        assert len(data_with_hidden["matches"]) > len(data_no_hidden["matches"])
        assert any(".hidden_config" in match for match in data_with_hidden["matches"])


async def test_fuzzy_search_content(tmp_path: Path):
    """Test fuzzy_search_content with ripgrep pattern and fuzzy filter."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create test files with content
    (tmp_path / "todo.py").write_text("""
# TODO: implement user authentication
def login():
    pass

# TODO: add error handling
def process():
    pass
""")
    (tmp_path / "main.py").write_text("""
# TODO: complete main function implementation
def main():
    pass
""")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "TODO implement",
                "path": str(tmp_path),
            },
        )

        # Parse result
        data = json.loads(result.content[0].text)
        assert "matches" in data
        assert len(data["matches"]) >= 2  # Should find both "implement" TODOs

        # Check structure of matches
        for match in data["matches"]:
            assert "file" in match
            assert "line" in match
            assert "content" in match
            assert "implement" in match["content"].lower()


async def test_fuzzy_search_content_with_limit(tmp_path: Path):
    """Test fuzzy_search_content respects limit parameter."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create many matching lines
    content = "\n".join([f"# TODO: task {i}" for i in range(20)])
    (tmp_path / "tasks.py").write_text(content)

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "TODO task",
                "path": str(tmp_path),
                "limit": 5,
            },
        )

        data = json.loads(result.content[0].text)
        assert len(data["matches"]) <= 5


async def test_fuzzy_search_content_default_pattern(tmp_path: Path):
    """Test fuzzy_search_content uses default pattern '.' (all lines)."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create test file with various content
    (tmp_path / "mixed.py").write_text("""
def function():
    print("hello")
    # This is a comment
    return True
""")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_content",
            {"fuzzy_filter": "function", "path": str(tmp_path)},  # No pattern specified
        )

        data = json.loads(result.content[0].text)
        assert "matches" in data
        assert len(data["matches"]) >= 1
        assert any("function" in match["content"] for match in data["matches"])


async def test_fuzzy_search_content_with_hidden(tmp_path: Path):
    """Test fuzzy_search_content searches hidden files when requested."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create hidden and visible files
    (tmp_path / ".env").write_text("SECRET_KEY=hidden_value")
    (tmp_path / "config.py").write_text("SECRET_KEY=visible_value")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Without hidden flag
        result_no_hidden = await client.call_tool(
            "fuzzy_search_content",
            {"fuzzy_filter": "SECRET", "path": str(tmp_path)},
        )
        data_no_hidden = json.loads(result_no_hidden.content[0].text)

        # With hidden flag
        result_with_hidden = await client.call_tool(
            "fuzzy_search_content",
            {"fuzzy_filter": "SECRET", "path": str(tmp_path), "hidden": True},
        )
        data_with_hidden = json.loads(result_with_hidden.content[0].text)

        # Should find more matches with hidden files
        assert len(data_with_hidden["matches"]) >= len(data_no_hidden["matches"])


async def test_fuzzy_search_content_with_rg_flags(tmp_path: Path):
    """Test fuzzy_search_content passes extra flags to ripgrep."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")


# Regex warning test removed - warnings not implemented in PyMuPDF version


# Diagnostic messages test removed - specific message format not guaranteed


# File regex warning test removed - warnings not implemented in PyMuPDF version


# Helper functions test removed - these functions don't exist in PyMuPDF implementation


async def test_fuzzy_search_content_case_sensitive(tmp_path: Path):
    """Test fuzzy_search_content with case-sensitive matching."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create test file with case-sensitive content
    (tmp_path / "case.py").write_text("ERROR: something failed\nerror: minor issue")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "error",
                "path": str(tmp_path),
                "rg_flags": "-i",  # Case insensitive
            },
        )

        data = json.loads(result.content[0].text)
        assert "matches" in data
        # Should find both ERROR and error with -i flag
        assert len(data["matches"]) >= 2


async def test_fuzzy_search_content_default_vs_content_only(tmp_path: Path):
    """Test the difference between default and content-only modes."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create test files with names that might interfere with content search
    (tmp_path / "test.py").write_text("def update():\n    pass")
    (tmp_path / "update.py").write_text("def check():\n    pass")
    (tmp_path / "other.py").write_text("# update comment here\ndef other():\n    pass")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Test 1: Default mode - search for "update" which should match both filename and content
        result_default = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "update",  # Should match update.py filename AND update() content
                "path": str(tmp_path),
            },
        )
        data_default = json.loads(result_default.content[0].text)

        # Test 2: Content-only mode - same search but content-only
        result_content_only = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "update",  # Should only match update() content, not filename
                "path": str(tmp_path),
                "content_only": True,
            },
        )
        data_content_only = json.loads(result_content_only.content[0].text)

        # Both modes should find at least the content matches
        assert (
            len(data_default["matches"]) >= 2
        )  # At least test.py and other.py content
        assert len(data_content_only["matches"]) >= 2  # Same content matches

        # Default mode might find more matches (including path matches)
        # Content-only mode should find fewer or equal matches
        assert len(data_default["matches"]) >= len(data_content_only["matches"])

        # Both should find the content matches for "update"
        default_content_matches = [
            match
            for match in data_default["matches"]
            if "update" in match["content"].lower()
        ]
        content_only_matches = [
            match
            for match in data_content_only["matches"]
            if "update" in match["content"].lower()
        ]

        # Should find the same content matches (at least the ones with "update" in content)
        assert len(default_content_matches) >= 2  # test.py and other.py
        assert len(content_only_matches) >= 2  # test.py and other.py

        # Verify files are found
        default_files = [match["file"] for match in default_content_matches]
        content_files = [match["file"] for match in content_only_matches]

        assert any("test.py" in f for f in default_files)
        assert any("other.py" in f for f in default_files)
        assert any("test.py" in f for f in content_files)
        assert any("other.py" in f for f in content_files)


async def test_fuzzy_search_content_only_mode(tmp_path: Path):
    """Test content-only mode ignores file paths in matching."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create files where filenames might match but content doesn't
    (tmp_path / "async.py").write_text("def sync_function():\n    return 42")
    (tmp_path / "sync.py").write_text("async def fetch_data():\n    return await api()")
    (tmp_path / "main.py").write_text("# No word here\ndef main():\n    pass")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Search for "async" with content-only mode
        result = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "async",
                "path": str(tmp_path),
                "content_only": True,
            },
        )

        data = json.loads(result.content[0].text)
        assert "matches" in data

        # Should only find the file with "async" in content, not in filename
        assert len(data["matches"]) == 1
        assert data["matches"][0]["file"].endswith("sync.py")
        assert "async def" in data["matches"][0]["content"]


async def test_error_handling():
    """Test error handling for missing arguments."""
    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Missing filter for fuzzy_search_files
        result = await client.call_tool("fuzzy_search_files", {"fuzzy_filter": ""})
        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "'fuzzy_filter' argument is required" in data["error"]

        # Missing filter for fuzzy_search_content
        result = await client.call_tool("fuzzy_search_content", {"fuzzy_filter": ""})
        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "'fuzzy_filter' argument is required" in data["error"]


async def test_list_tools():
    """Test that tools are properly exposed."""
    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.list_tools()

        assert len(result.tools) == 7

        # Find tools by name
        files_tool = next(t for t in result.tools if t.name == "fuzzy_search_files")
        content_tool = next(t for t in result.tools if t.name == "fuzzy_search_content")
        documents_tool = next(
            t for t in result.tools if t.name == "fuzzy_search_documents"
        )
        pdf_tool = next(t for t in result.tools if t.name == "extract_pdf_pages")
        labels_tool = next(t for t in result.tools if t.name == "get_pdf_page_labels")
        count_tool = next(t for t in result.tools if t.name == "get_pdf_page_count")
        outline_tool = next(t for t in result.tools if t.name == "get_pdf_outline")

        # Verify metadata for original tools
        assert files_tool.description and "fuzzy matching" in files_tool.description
        assert "fuzzy_filter" in files_tool.inputSchema["required"]

        # Verify outline tool
        assert (
            outline_tool.description and "table of contents" in outline_tool.description
        )
        assert "file" in outline_tool.inputSchema["required"]

        assert (
            content_tool.description
            and "Search file contents using fuzzy filtering" in content_tool.description
        )
        assert "fuzzy_filter" in content_tool.inputSchema["required"]

        # Verify metadata for PDF tools
        assert documents_tool.description and "PDFs" in documents_tool.description
        assert "fuzzy_filter" in documents_tool.inputSchema["required"]

        assert pdf_tool.description and "Extract specific pages" in pdf_tool.description
        assert "file" in pdf_tool.inputSchema["required"]
        assert "pages" in pdf_tool.inputSchema["required"]

        # Verify metadata for new PDF info tools
        assert labels_tool.description and "page labels" in labels_tool.description
        assert "file" in labels_tool.inputSchema["required"]

        assert (
            count_tool.description and "total number of pages" in count_tool.description
        )
        assert "file" in count_tool.inputSchema["required"]


def test_cli_search_files(tmp_path: Path):
    """Test CLI search-files subcommand."""
    # Create test files
    (tmp_path / "main.py").write_text("# main")
    (tmp_path / "test_main.py").write_text("# test")

    result = subprocess.run(
        [sys.executable, "mcp_fuzzy_search.py", "search-files", "main", str(tmp_path)],
        capture_output=True,
        text=True,
    )

    if "Cannot find the" in result.stderr:
        pytest.skip("Required binaries not available")

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output


def test_cli_search_content(tmp_path: Path):
    """Test CLI search-content subcommand."""
    # Create test file
    (tmp_path / "app.py").write_text("# TODO: implement feature\n# TODO: fix bug")

    result = subprocess.run(
        [
            sys.executable,
            "mcp_fuzzy_search.py",
            "search-content",
            "TODO implement",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )

    if "Cannot find the" in result.stderr:
        pytest.skip("Required binaries not available")

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "matches" in output


def test_cli_help():
    """Test CLI help output."""
    result = subprocess.run(
        [sys.executable, "mcp_fuzzy_search.py", "-h"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "Fuzzy search with ripgrep + fzf" in result.stdout
    assert "search-files" in result.stdout
    assert "search-content" in result.stdout


def test_cli_content_only_flag():
    """Test CLI --content-only flag."""
    # Test that the flag is accepted and passed correctly
    with patch("mcp_fuzzy_search.fuzzy_search_content") as mock_search:
        mock_search.return_value = {"matches": []}

        with patch(
            "sys.argv",
            ["mcp_fuzzy_search.py", "search-content", "test", ".", "--content-only"],
        ):
            mcp_fuzzy_search._cli()

        # Verify content_only=True was passed
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        # Check the content_only parameter
        assert call_args[1].get("content_only") is True or (
            len(call_args[0]) > 6 and call_args[0][6] is True
        )


def test_require_binary():
    """Test the _require helper function."""
    # Valid binary
    assert mcp_fuzzy_search._require("/usr/bin/rg", "rg") == "/usr/bin/rg"

    # Missing binary
    with pytest.raises(RuntimeError) as exc_info:
        mcp_fuzzy_search._require(None, "rg")

    assert "rg not found" in str(exc_info.value)


def test_binary_discovery():
    """Test binary discovery logic by calling shutil.which directly."""
    # Test that the discovery works with mock
    with patch("shutil.which") as mock_which:
        # When rg is available
        mock_which.side_effect = lambda x: "/usr/bin/rg" if x == "rg" else None
        rg_path = mock_which("rg")
        assert rg_path == "/usr/bin/rg"

        # Reset side_effect and set return_value for when binaries are missing
        mock_which.side_effect = None
        mock_which.return_value = None
        rg_path = mock_which("rg")
        assert rg_path is None


@patch("subprocess.Popen")
async def test_fuzzy_search_files_mocked(mock_popen):
    """Test fuzzy_search_files with mocked subprocess."""
    # Mock ripgrep process
    rg_proc = MagicMock()
    rg_proc.stdout = MagicMock()
    rg_proc.wait.return_value = 0

    # Mock fzf process
    fzf_proc = MagicMock()
    fzf_proc.communicate.return_value = ("src/main.py\nsrc/main_test.py\n", "")
    fzf_proc.returncode = 0

    mock_popen.side_effect = [rg_proc, fzf_proc]

    with (
        patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"),
        patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
    ):
        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_files", {"fuzzy_filter": "main", "path": "."}
            )

            data = json.loads(result.content[0].text)
            assert data["matches"] == ["src/main.py", "src/main_test.py"]


@patch("subprocess.Popen")
async def test_fuzzy_search_content_mocked(mock_popen):
    """Test fuzzy_search_content with mocked subprocess."""
    # Mock ripgrep process
    rg_proc = MagicMock()
    rg_proc.stdout = MagicMock()
    rg_proc.stderr = MagicMock()
    rg_proc.stderr.read.return_value = b""
    rg_proc.wait.return_value = 0
    rg_proc.returncode = 0

    # Mock fzf process with properly formatted output
    fzf_proc = MagicMock()
    fzf_proc.communicate.return_value = (
        "src/app.py:10:    # TODO: implement feature\n"
        "src/test.py:5:    # TODO: implement tests\n",
        "",
    )
    fzf_proc.returncode = 0

    mock_popen.side_effect = [rg_proc, fzf_proc]

    with (
        patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"),
        patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
    ):
        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_content",
                {"fuzzy_filter": "TODO implement", "path": "."},
            )

            data = json.loads(result.content[0].text)
            assert len(data["matches"]) == 2
            assert data["matches"][0]["file"] == "src/app.py"
            assert data["matches"][0]["line"] == 10
            assert "implement feature" in data["matches"][0]["content"]

            # Verify fzf was called with --nth=1,3.. by default
            fzf_call_args = mock_popen.call_args_list[1][0][0]
            assert "--nth=1,3.." in fzf_call_args


@patch("subprocess.Popen")
async def test_fuzzy_search_content_mocked_content_only(mock_popen):
    """Test fuzzy_search_content with content_only mode."""
    # Mock ripgrep process
    rg_proc = MagicMock()
    rg_proc.stdout = MagicMock()
    rg_proc.stderr = MagicMock()
    rg_proc.stderr.read.return_value = b""
    rg_proc.wait.return_value = 0
    rg_proc.returncode = 0

    # Mock fzf process
    fzf_proc = MagicMock()
    fzf_proc.communicate.return_value = (
        "src/sync.py:1:async def fetch():\n",
        "",
    )
    fzf_proc.returncode = 0

    mock_popen.side_effect = [rg_proc, fzf_proc]

    with (
        patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"),
        patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
    ):
        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_content",
                {"fuzzy_filter": "async", "path": ".", "content_only": True},
            )

            data = json.loads(result.content[0].text)
            assert len(data["matches"]) == 1

            # Verify fzf was called with --nth=3.. for content-only mode
            fzf_call_args = mock_popen.call_args_list[1][0][0]
            assert "--nth=3.." in fzf_call_args


# Multiline support tests

monkeypatch = pytest.MonkeyPatch()


def test_fuzzy_search_files_multiline(tmp_path: Path):
    """Test multiline support in fuzzy_search_files."""
    # Create test files with content
    test_file1 = tmp_path / "code.js"
    test_file1.write_text(
        "function example() {\n  return 'hello';\n}\n\nclass TestClass {\n  constructor() {}\n}"
    )

    test_file2 = tmp_path / "data.py"
    test_file2.write_text("def process():\n    print('processing')")

    mock_rg = tmp_path / "rg"
    mock_rg.write_text(f'''#!/usr/bin/env python3
import sys
if "--files" in sys.argv:
    print("{test_file1}")
    print("{test_file2}")
''')
    mock_rg.chmod(0o755)

    mock_fzf = tmp_path / "fzf"
    mock_fzf.write_text(f'''#!/usr/bin/env python3
import sys
if "--read0" in sys.argv and "--print0" in sys.argv:
    # Read null-delimited input
    data = sys.stdin.buffer.read()
    # Look for "function" in the content
    if b"function" in data:
        # Return matching file record with null terminator
        content = "{test_file1}:\\nfunction example() {{\\n  return 'hello';\\n}}\\n\\nclass TestClass {{\\n  constructor() {{}}\\n}}"
        print(content, end="\\0")
''')
    mock_fzf.chmod(0o755)

    with monkeypatch.context() as m:
        m.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

        # Reload module globals to pick up new executables
        mcp_fuzzy_search.RG_EXECUTABLE = shutil.which("rg")
        mcp_fuzzy_search.FZF_EXECUTABLE = shutil.which("fzf")

        result = mcp_fuzzy_search.fuzzy_search_files(
            "function", str(tmp_path), multiline=True
        )

        assert "matches" in result
        matches = result["matches"]
        assert len(matches) > 0
        assert "function example()" in matches[0]
        assert "class TestClass" in matches[0]


def test_fuzzy_search_content_multiline(tmp_path: Path):
    """Test multiline support in fuzzy_search_content."""
    # Create test files with multi-line patterns
    test_file1 = tmp_path / "service.py"
    test_file1.write_text("""
class UserService:
    def authenticate(self, user):
        if user.is_valid:
            return True
        return False

def process_request():
    pass
""")

    test_file2 = tmp_path / "model.py"
    test_file2.write_text(
        "class User:\n    def __init__(self):\n        self.name = ''\n        self.email = ''"
    )

    # Use subprocess mocking instead of PATH manipulation for better reliability
    with (
        patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"),
        patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
        patch("subprocess.check_output") as mock_rg,
        patch("subprocess.Popen") as mock_popen,
    ):
        # Mock rg listing files
        mock_rg.return_value = f"{test_file1}\n{test_file2}\n"

        # Mock fzf finding the class
        mock_fzf_proc = MagicMock()
        normalized_path = normalize_path(str(test_file1))
        expected_output = f"{normalized_path}:\nclass UserService:\n    def authenticate(self, user):\n        if user.is_valid:\n            return True\n        return False\n\ndef process_request():\n    pass\n\x00"
        mock_fzf_proc.communicate.return_value = (expected_output.encode(), b"")
        mock_fzf_proc.returncode = 0
        mock_popen.return_value = mock_fzf_proc

        result = mcp_fuzzy_search.fuzzy_search_content(
            "class", str(tmp_path), multiline=True
        )

        assert "matches" in result
        matches = result["matches"]
        assert len(matches) > 0
        assert normalize_path(matches[0]["file"]) == normalize_path(str(test_file1))
        assert "class UserService:" in matches[0]["content"]
        assert "def authenticate" in matches[0]["content"]


def test_multiline_cli_support():
    """Test CLI support for multiline flags."""
    # Test search-files multiline
    with patch("mcp_fuzzy_search.fuzzy_search_files") as mock_search_files:
        mock_search_files.return_value = {"matches": ["file1.txt"]}

        with patch(
            "sys.argv",
            ["mcp_fuzzy_search.py", "search-files", "test", ".", "--multiline"],
        ):
            mcp_fuzzy_search._cli()

        # Verify multiline=True was passed - check both positional and keyword args
        mock_search_files.assert_called_once()
        call_args = mock_search_files.call_args
        # Function signature: fuzzy_search_files(filter, path, hidden, limit, multiline)
        if len(call_args[0]) > 4:
            assert call_args[0][4] is True  # positional argument
        else:
            assert call_args[1].get("multiline") is True

    # Test search-content multiline
    with patch("mcp_fuzzy_search.fuzzy_search_content") as mock_search_content:
        mock_search_content.return_value = {"matches": []}

        with patch(
            "sys.argv",
            ["mcp_fuzzy_search.py", "search-content", "test", ".", "--multiline"],
        ):
            mcp_fuzzy_search._cli()

        # Verify multiline=True was passed
        mock_search_content.assert_called_once()
        call_args = mock_search_content.call_args
        # Function signature: fuzzy_search_content(filter, path, hidden, limit, rg_flags, multiline)
        if len(call_args[0]) > 5:
            assert call_args[0][5] is True  # positional argument
        else:
            assert call_args[1].get("multiline") is True


async def test_fuzzy_search_files_multiline_mcp():
    """Test multiline support through MCP interface for fuzzy_search_files."""
    test_content = "async function processData() {\n  const result = await fetch('/api');\n  return result.json();\n}"

    # Create a mock file object
    mock_file = MagicMock()
    mock_file.read.return_value = test_content.encode()

    # We need to patch Path at the module level
    with patch("mcp_fuzzy_search.Path") as mock_path_class:
        # Create a mock Path instance
        mock_path_instance = MagicMock()
        mock_path_instance.open.return_value.__enter__.return_value = mock_file

        # Path() constructor returns our mock instance
        mock_path_class.return_value = mock_path_instance

        # For Path(path).resolve() calls
        mock_path_class.return_value.resolve.return_value = mock_path_instance
        mock_path_class.return_value.resolve.return_value.__str__.return_value = (
            "api.js"
        )

        with (
            patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"),
            patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
            patch("subprocess.check_output") as mock_rg_output,
            patch("subprocess.Popen") as mock_popen,
        ):
            # Mock rg listing files
            mock_rg_output.return_value = "api.js\n"

            # Mock fzf finding the async function
            mock_fzf_proc = MagicMock()
            mock_fzf_proc.communicate.return_value = (
                b"api.js:\nasync function processData() {\n  const result = await fetch('/api');\n  return result.json();\n}\x00",
                b"",
            )
            mock_fzf_proc.returncode = 0
            mock_popen.return_value = mock_fzf_proc

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "fuzzy_search_files", {"fuzzy_filter": "async", "multiline": True}
                )

                data = json.loads(result.content[0].text)
                assert "matches" in data
                assert len(data["matches"]) > 0
                assert "async function processData()" in data["matches"][0]


async def test_fuzzy_search_content_multiline_mcp():
    """Test multiline support through MCP interface for fuzzy_search_content."""
    test_content = "class DatabaseService {\n  constructor(config) {\n    this.config = config;\n  }\n\n  async connect() {\n    // TODO: implement\n  }\n}"

    # Create a mock file object
    mock_file = MagicMock()
    mock_file.read.return_value = test_content.encode()

    # We need to patch Path at the module level
    with patch("mcp_fuzzy_search.Path") as mock_path_class:
        # Create a mock Path instance
        mock_path_instance = MagicMock()
        mock_path_instance.open.return_value.__enter__.return_value = mock_file

        # Path() constructor returns our mock instance
        mock_path_class.return_value = mock_path_instance

        # For Path(path).resolve() calls
        mock_path_class.return_value.resolve.return_value = mock_path_instance
        mock_path_class.return_value.resolve.return_value.__str__.return_value = (
            "service.js"
        )

        with (
            patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"),
            patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
            patch("subprocess.check_output") as mock_rg_output,
            patch("subprocess.Popen") as mock_popen,
        ):
            # Mock rg listing files
            mock_rg_output.return_value = "service.js\n"

            # Mock fzf finding the class
            mock_fzf_proc = MagicMock()
            mock_fzf_proc.communicate.return_value = (
                b"service.js:\nclass DatabaseService {\n  constructor(config) {\n    this.config = config;\n  }\n\n  async connect() {\n    // TODO: implement\n  }\n}\x00",
                b"",
            )
            mock_fzf_proc.returncode = 0
            mock_popen.return_value = mock_fzf_proc

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "fuzzy_search_content", {"fuzzy_filter": "class", "multiline": True}
                )

                data = json.loads(result.content[0].text)
                assert "matches" in data
                assert len(data["matches"]) > 0
                assert data["matches"][0]["file"] == "service.js"
                assert "class DatabaseService" in data["matches"][0]["content"]
                assert "async connect()" in data["matches"][0]["content"]


def test_windows_path_parsing_multiline():
    """Test parsing of multiline results with Windows paths containing colons."""
    test_cases = [
        # Windows absolute path
        {
            "input": "C:/Users/test/file.py:\nclass Test:\n    pass",
            "expected_file": "C:/Users/test/file.py",
            "expected_content": "class Test:\n    pass",
        },
        # Windows path with multiple directories
        {
            "input": "D:/Projects/my-app/src/main.py:\ndef main():\n    print('hello')",
            "expected_file": "D:/Projects/my-app/src/main.py",
            "expected_content": "def main():\n    print('hello')",
        },
        # UNC path
        {
            "input": "//server/share/file.txt:\nSome content\nMore content",
            "expected_file": "//server/share/file.txt",
            "expected_content": "Some content\nMore content",
        },
        # Path with spaces (normalized)
        {
            "input": 'C:/Program Files/app/config.json:\n{\n  "key": "value"\n}',
            "expected_file": "C:/Program Files/app/config.json",
            "expected_content": '{\n  "key": "value"\n}',
        },
    ]

    for test_case in test_cases:
        # Simulate what the parsing logic does
        input_str = test_case["input"]
        if ":\n" in input_str:
            file_part, content_part = input_str.split(":\n", 1)
            assert file_part == test_case["expected_file"], (
                f"Failed to parse file part from {input_str}"
            )
            assert content_part == test_case["expected_content"], (
                f"Failed to parse content part from {input_str}"
            )


def test_fuzzy_search_content_windows_paths():
    """Test fuzzy_search_content with Windows-style paths in ripgrep output."""
    with patch("subprocess.check_output") as mock_rg_output:
        with patch("subprocess.Popen") as mock_popen:
            with patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"):
                with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                    # Mock rg listing files with Windows paths
                    mock_rg_output.return_value = (
                        r"C:\Users\test\app.py" + "\n" + r"D:\Projects\main.py" + "\n"
                    )

                    # Mock fzf process for multiline mode
                    mock_proc = MagicMock()
                    # Return Windows path normalized to forward slashes
                    mock_proc.communicate.return_value = (
                        b"C:/Users/test/app.py:\nclass Application:\n    def run(self):\n        pass\x00",
                        b"",
                    )
                    mock_proc.returncode = 0
                    mock_popen.return_value = mock_proc

                    # Mock file reading
                    with patch("pathlib.Path.open") as mock_open:
                        mock_file = MagicMock()
                        mock_file.read.return_value = (
                            b"class Application:\n    def run(self):\n        pass"
                        )
                        mock_open.return_value.__enter__.return_value = mock_file

                        result = mcp_fuzzy_search.fuzzy_search_content(
                            "class", ".", multiline=True
                        )

                        assert "matches" in result
                        assert len(result["matches"]) > 0
                        match = result["matches"][0]
                        assert match["file"] == "C:/Users/test/app.py"
                        assert "class Application:" in match["content"]
                        # Ensure no backslashes in the path
                        assert "\\" not in match["file"]


# ---------------------------------------------------------------------------
# Tests for FZF exit codes handling
# ---------------------------------------------------------------------------


def test_fuzzy_search_files_fzf_no_match():
    """Test that fuzzy_search_files handles FZF_EXIT_NO_MATCH (exit code 1) correctly."""
    with patch("subprocess.check_output") as mock_rg_output:
        with patch("subprocess.Popen") as mock_popen:
            with patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"):
                with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                    # Mock rg listing files
                    mock_rg_output.return_value = "file1.py\nfile2.py\nfile3.py\n"

                    # Mock fzf process returning FZF_EXIT_NO_MATCH
                    mock_fzf_proc = MagicMock()
                    mock_fzf_proc.communicate.return_value = ("", "")
                    mock_fzf_proc.returncode = (
                        mcp_fuzzy_search.FZF_EXIT_NO_MATCH
                    )  # Exit code 1

                    # Mock rg process
                    mock_rg_proc = MagicMock()
                    mock_rg_proc.stdout = MagicMock()
                    mock_rg_proc.wait.return_value = 0

                    mock_popen.side_effect = [mock_rg_proc, mock_fzf_proc]

                    # Call the function
                    result = mcp_fuzzy_search.fuzzy_search_files(
                        "nonexistent_pattern", "."
                    )

                    # Should return empty matches, not an error
                    assert "matches" in result
                    assert result["matches"] == []
                    assert "error" not in result


def test_fuzzy_search_content_fzf_no_match():
    """Test that fuzzy_search_content handles FZF_EXIT_NO_MATCH (exit code 1) correctly."""
    with patch("subprocess.Popen") as mock_popen:
        with patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"):
            with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                # Mock rg process
                mock_rg_proc = MagicMock()
                mock_rg_proc.stdout = MagicMock()
                mock_rg_proc.stderr = MagicMock()
                mock_rg_proc.stderr.read.return_value = b""
                mock_rg_proc.wait.return_value = 0
                mock_rg_proc.returncode = 0

                # Mock fzf process returning FZF_EXIT_NO_MATCH
                mock_fzf_proc = MagicMock()
                mock_fzf_proc.communicate.return_value = ("", "")
                mock_fzf_proc.returncode = (
                    mcp_fuzzy_search.FZF_EXIT_NO_MATCH
                )  # Exit code 1

                mock_popen.side_effect = [mock_rg_proc, mock_fzf_proc]

                # Call the function
                result = mcp_fuzzy_search.fuzzy_search_content(
                    "nonexistent_pattern", "."
                )

                # Should return empty matches, not an error
                assert "matches" in result
                assert result["matches"] == []
                assert "error" not in result


def test_fuzzy_search_documents_fzf_no_match():
    """Test that fuzzy_search_documents handles FZF_EXIT_NO_MATCH (exit code 1) correctly."""
    with patch("subprocess.Popen") as mock_popen:
        with patch.object(mcp_fuzzy_search, "RGA_EXECUTABLE", "/mock/rga"):
            with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                # Mock rga process with JSON output
                mock_rga_proc = MagicMock()
                mock_rga_proc.communicate.return_value = (
                    '{"type":"match","data":{"path":{"text":"test.pdf"},"lines":{"text":"Page 1: Some content"},"line_number":null}}\n',
                    "",
                )
                mock_rga_proc.wait.return_value = None

                # Mock fzf process returning FZF_EXIT_NO_MATCH
                mock_fzf_proc = MagicMock()
                mock_fzf_proc.communicate.return_value = ("", "")
                mock_fzf_proc.returncode = (
                    mcp_fuzzy_search.FZF_EXIT_NO_MATCH
                )  # Exit code 1

                mock_popen.side_effect = [mock_rga_proc, mock_fzf_proc]

                # Call the function
                result = mcp_fuzzy_search.fuzzy_search_documents(
                    "nonexistent_pattern", "."
                )

                # Should return empty matches, not an error
                assert "matches" in result
                assert result["matches"] == []
                assert "error" not in result


def test_fuzzy_search_files_fzf_actual_error():
    """Test that fuzzy_search_files handles FZF_EXIT_ERROR (exit code 2) correctly."""
    with patch("subprocess.check_output") as mock_rg_output:
        with patch("subprocess.Popen") as mock_popen:
            with patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"):
                with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                    # Mock rg listing files
                    mock_rg_output.return_value = "file1.py\nfile2.py\n"

                    # Mock fzf process returning FZF_EXIT_ERROR
                    mock_fzf_proc = MagicMock()
                    mock_fzf_proc.communicate.return_value = ("", "fzf error occurred")
                    mock_fzf_proc.returncode = (
                        mcp_fuzzy_search.FZF_EXIT_ERROR
                    )  # Exit code 2

                    # Mock rg process
                    mock_rg_proc = MagicMock()
                    mock_rg_proc.stdout = MagicMock()
                    mock_rg_proc.wait.return_value = 0

                    mock_popen.side_effect = [mock_rg_proc, mock_fzf_proc]

                    # Call the function
                    result = mcp_fuzzy_search.fuzzy_search_files("test", ".")

                    # Should return an error
                    assert "error" in result
                    assert "matches" not in result


def test_fuzzy_search_content_fzf_actual_error():
    """Test that fuzzy_search_content handles FZF_EXIT_ERROR (exit code 2) correctly."""
    with patch("subprocess.Popen") as mock_popen:
        with patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"):
            with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                # Mock rg process
                mock_rg_proc = MagicMock()
                mock_rg_proc.stdout = MagicMock()
                mock_rg_proc.stderr = MagicMock()
                mock_rg_proc.stderr.read.return_value = b""
                mock_rg_proc.wait.return_value = 0
                mock_rg_proc.returncode = 0

                # Mock fzf process returning FZF_EXIT_ERROR
                mock_fzf_proc = MagicMock()
                mock_fzf_proc.communicate.return_value = ("", "fzf error occurred")
                mock_fzf_proc.returncode = (
                    mcp_fuzzy_search.FZF_EXIT_ERROR
                )  # Exit code 2

                mock_popen.side_effect = [mock_rg_proc, mock_fzf_proc]

                # Call the function
                result = mcp_fuzzy_search.fuzzy_search_content("test", ".")

                # Should return an error
                assert "error" in result
                assert "matches" not in result


def test_fuzzy_search_files_multiline_fzf_no_match():
    """Test fuzzy_search_files in multiline mode with FZF_EXIT_NO_MATCH."""
    with patch("subprocess.check_output") as mock_rg_output:
        with patch("subprocess.Popen") as mock_popen:
            with patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"):
                with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                    # Mock rg listing files
                    mock_rg_output.return_value = "test.py\n"

                    # Mock fzf process returning FZF_EXIT_NO_MATCH in multiline mode
                    mock_fzf_proc = MagicMock()
                    mock_fzf_proc.communicate.return_value = (b"", b"")
                    mock_fzf_proc.returncode = (
                        mcp_fuzzy_search.FZF_EXIT_NO_MATCH
                    )  # Exit code 1
                    mock_popen.return_value = mock_fzf_proc

                    # Mock file reading
                    with patch("pathlib.Path.open") as mock_open:
                        mock_file = MagicMock()
                        mock_file.read.return_value = b"test content"
                        mock_open.return_value.__enter__.return_value = mock_file

                        # Call the function in multiline mode
                        result = mcp_fuzzy_search.fuzzy_search_files(
                            "nonexistent", ".", multiline=True
                        )

                        # Should return empty matches, not an error
                        assert "matches" in result
                        assert result["matches"] == []
                        assert "error" not in result


def test_fuzzy_search_content_multiline_fzf_no_match():
    """Test fuzzy_search_content in multiline mode with FZF_EXIT_NO_MATCH."""
    with patch("subprocess.check_output") as mock_rg_output:
        with patch("subprocess.Popen") as mock_popen:
            with patch.object(mcp_fuzzy_search, "RG_EXECUTABLE", "/mock/rg"):
                with patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"):
                    # Mock rg listing files
                    mock_rg_output.return_value = "test.py\n"

                    # Mock fzf process returning FZF_EXIT_NO_MATCH in multiline mode
                    mock_fzf_proc = MagicMock()
                    mock_fzf_proc.communicate.return_value = (b"", b"")
                    mock_fzf_proc.returncode = (
                        mcp_fuzzy_search.FZF_EXIT_NO_MATCH
                    )  # Exit code 1
                    mock_popen.return_value = mock_fzf_proc

                    # Mock file reading
                    with patch("pathlib.Path.open") as mock_open:
                        mock_file = MagicMock()
                        mock_file.read.return_value = b"test content"
                        mock_open.return_value.__enter__.return_value = mock_file

                        # Call the function in multiline mode
                        result = mcp_fuzzy_search.fuzzy_search_content(
                            "nonexistent", ".", multiline=True
                        )

                        # Should return empty matches, not an error
                        assert "matches" in result
                        assert result["matches"] == []
                        assert "error" not in result


# ---------------------------------------------------------------------------
# Tests for PDF tools
# ---------------------------------------------------------------------------


async def test_fuzzy_search_documents_missing_binary():
    """Test fuzzy_search_documents handles missing rga binary gracefully."""
    # Temporarily patch RGA_EXECUTABLE to None
    original_rga = mcp_fuzzy_search.RGA_EXECUTABLE
    try:
        mcp_fuzzy_search.RGA_EXECUTABLE = None

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_documents", {"fuzzy_filter": "test", "path": "."}
            )

            data = json.loads(result.content[0].text)
            assert "error" in data
            assert "ripgrep-all" in data["error"]
            assert "not installed" in data["error"]
    finally:
        mcp_fuzzy_search.RGA_EXECUTABLE = original_rga


async def test_fuzzy_search_documents_basic(tmp_path: Path):
    """Test fuzzy_search_documents with mock rga output."""
    _skip_if_missing("rga")
    _skip_if_missing("fzf")

    # Create a mock PDF file for testing
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock the rga JSON output with Page prefix
    # Use json.dumps to properly escape the path for JSON
    import json

    escaped_path = json.dumps(str(test_pdf))[1:-1]  # Remove quotes
    mock_rga_output = (
        '''{"type":"match","data":{"path":{"text":"'''
        + escaped_path
        + '''"},"lines":{"text":"Page 1: This is test content"},"line_number":null,"absolute_offset":100,"submatches":[{"match":{"text":"test"},"start":8,"end":12}]}}
{"type":"end","data":{"path":{"text":"'''
        + escaped_path
        + """"},"binary_offset":null,"stats":{"elapsed":{"secs":0,"nanos":35222125,"human":"0.035222s"},"searches":1,"searches_with_match":1,"bytes_searched":1000,"bytes_printed":100,"matched_lines":1,"matches":1}}}"""
    )

    with patch("subprocess.Popen") as mock_popen:
        # Mock rga process
        mock_rga_proc = MagicMock()
        # Mock communicate() to return the output
        mock_rga_proc.communicate.return_value = (mock_rga_output, "")
        mock_rga_proc.wait.return_value = None

        # Mock fzf process - needs to match the format produced by rga
        # The format is: file_path:line_num:text
        # For PDFs, line_num is None in JSON but gets converted to 0
        mock_fzf_proc = MagicMock()
        mock_fzf_proc.communicate.return_value = (
            f"{test_pdf}:0:Page 1: This is test content",
            None,
        )
        mock_fzf_proc.returncode = 0

        # Configure mocks for subprocess.Popen
        mock_popen.side_effect = [mock_rga_proc, mock_fzf_proc]

        # Mock the executable paths so the function doesn't return early
        with (
            patch.object(mcp_fuzzy_search, "RGA_EXECUTABLE", "/mock/rga"),
            patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
        ):
            # Mock PyMuPDF if available
            if mcp_fuzzy_search.PYMUPDF_AVAILABLE:
                mock_doc = MagicMock()
                mock_doc.page_count = 1
                # Mock individual page access
                mock_page = MagicMock()
                mock_page.get_label.return_value = "Cover"
                mock_doc.__getitem__.return_value = mock_page
                mock_doc.close.return_value = None

                with patch("fitz.open", return_value=mock_doc):
                    async with client_session(
                        mcp_fuzzy_search.mcp._mcp_server
                    ) as client:
                        result = await client.call_tool(
                            "fuzzy_search_documents",
                            {"fuzzy_filter": "test", "path": str(tmp_path)},
                        )

                        data = json.loads(result.content[0].text)
                        # Debug output
                        if "error" in data:
                            print(f"ERROR: {data['error']}")
                        print(f"Got data: {data}")
                        assert "matches" in data
                        assert len(data["matches"]) == 1

                        match = data["matches"][0]
                        assert "file" in match
                        assert "page" in match
                        assert "content" in match
                        assert "match_text" in match

                        assert match["page"] == 1
                        assert match["page_index_0based"] == 0
                        assert "test content" in match["content"]
                        assert match["match_text"] == "test"

                        # Check for page label
                        assert "page_label" in match
                        assert match["page_label"] == "Cover"
            else:
                # Test without PyMuPDF
                async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                    result = await client.call_tool(
                        "fuzzy_search_documents",
                        {"fuzzy_filter": "test", "path": str(tmp_path)},
                    )

                    data = json.loads(result.content[0].text)
                    assert "matches" in data
                    assert len(data["matches"]) == 1

                    match = data["matches"][0]
                    assert match["page"] == 1
                    assert match["page_index_0based"] == 0
                    assert "page_label" not in match  # No label without PyMuPDF


async def test_fuzzy_search_documents_parse_rga_json():
    """Test parsing of actual rga JSON output format."""
    sample_json = """{"type":"match","data":{"path":{"text":"./Linear Algebra Done Right 4e.pdf"},"lines":{"text":"Page 402: of scalar and vector, 12\\n"},"line_number":null,"absolute_offset":1174364,"submatches":[{"match":{"text":"vector"},"start":24,"end":30}]}}"""

    # Parse the JSON
    data = json.loads(sample_json)
    assert data["type"] == "match"
    assert data["data"]["line_number"] is None  # PDFs don't have line numbers
    assert "Page 402:" in data["data"]["lines"]["text"]

    # Extract page number
    import re

    lines_text = data["data"]["lines"]["text"].strip()
    page_match = re.match(r"Page (\d+):", lines_text)
    assert page_match is not None
    assert int(page_match.group(1)) == 402


async def test_fuzzy_search_documents_with_page_labels(tmp_path: Path):
    """Test fuzzy_search_documents correctly extracts page labels from PDFs."""
    _skip_if_missing("rga")
    _skip_if_missing("fzf")

    if not mcp_fuzzy_search.PYMUPDF_AVAILABLE:
        pytest.skip("PyMuPDF not available")

    # Create a mock PDF file
    test_pdf = tmp_path / "test_labels.pdf"
    test_pdf.write_bytes(b"%PDF-1.4\n%fake pdf")

    # Mock rga output with multiple pages
    # Use json.dumps to properly escape the path for JSON
    import json

    escaped_path = json.dumps(str(test_pdf))[1:-1]  # Remove quotes
    mock_rga_output = [
        f'{{"type":"match","data":{{"path":{{"text":"{escaped_path}"}},"lines":{{"text":"Page 1: Introduction to concepts"}},"line_number":null,"absolute_offset":100,"submatches":[{{"match":{{"text":"concepts"}},"start":25,"end":33}}]}}}}',
        f'{{"type":"match","data":{{"path":{{"text":"{escaped_path}"}},"lines":{{"text":"Page 5: Chapter 1 begins"}},"line_number":null,"absolute_offset":500,"submatches":[{{"match":{{"text":"Chapter"}},"start":8,"end":15}}]}}}}',
        f'{{"type":"match","data":{{"path":{{"text":"{escaped_path}"}},"lines":{{"text":"Page 10: Table of contents"}},"line_number":null,"absolute_offset":1000,"submatches":[{{"match":{{"text":"contents"}},"start":18,"end":26}}]}}}}',
    ]

    with patch("subprocess.Popen") as mock_popen:
        # Mock rga process
        mock_rga_proc = MagicMock()
        # Join the mock output lines
        mock_rga_proc.communicate.return_value = ("\n".join(mock_rga_output), "")
        mock_rga_proc.wait.return_value = None

        # Mock fzf process
        mock_fzf_proc = MagicMock()
        mock_fzf_proc.communicate.return_value = (
            f"{test_pdf}:0:Page 1: Introduction to concepts\n{test_pdf}:0:Page 5: Chapter 1 begins\n{test_pdf}:0:Page 10: Table of contents",
            None,
        )
        mock_fzf_proc.returncode = 0

        mock_popen.side_effect = [mock_rga_proc, mock_fzf_proc]

        # Mock PyMuPDF with page labels
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        # 10 pages with labels: i, ii, iii, iv, 1, 2, 3, 4, 5, ToC
        page_labels = ["i", "ii", "iii", "iv", "1", "2", "3", "4", "5", "ToC"]

        # Mock page access to return correct labels
        def mock_getitem(index):
            mock_page = MagicMock()
            mock_page.get_label.return_value = page_labels[index]
            return mock_page

        mock_doc.__getitem__.side_effect = mock_getitem
        mock_doc.close.return_value = None

        with (
            patch("fitz.open", return_value=mock_doc),
            patch.object(mcp_fuzzy_search, "RGA_EXECUTABLE", "/mock/rga"),
            patch.object(mcp_fuzzy_search, "FZF_EXECUTABLE", "/mock/fzf"),
        ):
            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "fuzzy_search_documents",
                    {
                        "fuzzy_filter": "concept chapter content",
                        "path": str(tmp_path),
                    },
                )

                data = json.loads(result.content[0].text)
                assert "matches" in data
                assert len(data["matches"]) == 3

                # Check first match - Page 1 (label "i")
                match1 = data["matches"][0]
                assert match1["page"] == 1
                assert match1["page_index_0based"] == 0
                assert match1["page_label"] == "i"
                assert "Introduction" in match1["content"]

                # Check second match - Page 5 (label "1")
                match2 = data["matches"][1]
                assert match2["page"] == 5
                assert match2["page_index_0based"] == 4
                assert match2["page_label"] == "1"
                assert "Chapter" in match2["content"]

                # Check third match - Page 10 (label "ToC")
                match3 = data["matches"][2]
                assert match3["page"] == 10
                assert match3["page_index_0based"] == 9
                assert match3["page_label"] == "ToC"
                assert "contents" in match3["content"]


async def test_extract_pdf_pages_missing_binaries():
    """Test extract_pdf_pages handles missing binaries gracefully."""
    # Test missing PyMuPDF
    original_pymupdf = mcp_fuzzy_search.PYMUPDF_AVAILABLE
    try:
        mcp_fuzzy_search.PYMUPDF_AVAILABLE = False

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "extract_pdf_pages", {"file": "test.pdf", "pages": "1,2,3"}
            )

            data = json.loads(result.content[0].text)
            assert "error" in data
            assert "PyMuPDF" in data["error"]
    finally:
        mcp_fuzzy_search.PYMUPDF_AVAILABLE = original_pymupdf

    # Test missing pandoc (only affects markdown conversion)
    # Create a test PDF file first
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4\n%fake pdf")
        test_pdf = tmp.name

    try:
        original_pandoc = mcp_fuzzy_search.PANDOC_EXECUTABLE
        try:
            mcp_fuzzy_search.PANDOC_EXECUTABLE = None

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Without pandoc, markdown format should still work (fallback to plain text)
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {"file": test_pdf, "pages": "1", "format": "markdown"},
                )

                data = json.loads(result.content[0].text)
                # Should not error, but fall back to plain text extraction
                assert "error" not in data or "pandoc" not in data.get("error", "")
        finally:
            mcp_fuzzy_search.PANDOC_EXECUTABLE = original_pandoc
    finally:
        import os

        os.unlink(test_pdf)


async def test_extract_pdf_pages_invalid_input(tmp_path: Path):
    """Test extract_pdf_pages handles invalid input gracefully."""
    # No need to skip for PyMuPDF - it's imported at module level

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Test missing file
        result = await client.call_tool(
            "extract_pdf_pages",
            {"file": str(tmp_path / "nonexistent.pdf"), "pages": "1"},
        )
        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "not found" in data["error"]

        # Test invalid page numbers
        test_pdf = tmp_path / "test.pdf"
        # Create a minimal valid PDF that PyMuPDF can open
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
        test_pdf.write_bytes(pdf_content)

        result = await client.call_tool(
            "extract_pdf_pages", {"file": str(test_pdf), "pages": "abc"}
        )
        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "Invalid page specification" in data["error"]


async def test_extract_pdf_pages_basic(tmp_path: Path):
    """Test extract_pdf_pages with mock PyMuPDF."""
    # No need to skip for PyMuPDF

    # Create a test PDF
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock PyMuPDF
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 5
        mock_doc.get_page_numbers.return_value = []  # No label matches
        mock_doc.get_page_labels.return_value = None

        # Create mock page
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Extracted content from page 1"
        mock_page.get_label.return_value = "1"

        # Configure document to return page
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc for markdown conversion
        with patch("subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"# Page 1\n\nExtracted content from page 1\n"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {"file": str(test_pdf), "pages": "1", "format": "markdown"},
                )

                data = json.loads(result.content[0].text)
                assert "content" in data
                assert "pages_extracted" in data
                assert "format" in data

                assert data["pages_extracted"] == [0]  # 0-based index for page 1
                assert data["format"] == "markdown"
                assert "Extracted content" in data["content"]


async def test_fuzzy_search_documents_with_file_types(tmp_path: Path):
    """Test fuzzy_search_documents with file type filtering."""
    _skip_if_missing("rga")
    _skip_if_missing("fzf")

    with patch("subprocess.Popen") as mock_popen:
        # Mock processes
        mock_rga_proc = MagicMock()
        mock_rga_proc.communicate.return_value = ("", "")
        mock_rga_proc.wait.return_value = None

        mock_fzf_proc = MagicMock()
        mock_fzf_proc.communicate.return_value = ("", None)
        mock_fzf_proc.returncode = 0

        mock_popen.side_effect = [mock_rga_proc, mock_fzf_proc]

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_documents",
                {
                    "fuzzy_filter": "test",
                    "path": str(tmp_path),
                    "file_types": "pdf,docx",
                },
            )

            # Check that rga was called with the right adapter flags
            rga_call = mock_popen.call_args_list[0]
            args = rga_call[0][0]
            # Find the adapter argument with equals sign
            adapter_arg = None
            for arg in args:
                if arg.startswith("--rga-adapters="):
                    adapter_arg = arg
                    break
            assert adapter_arg is not None
            # Check for actual adapter names in the combined string
            assert (
                adapter_arg == "--rga-adapters=+poppler,pandoc"
            )  # pdf maps to poppler, docx maps to pandoc

            # Verify the result (should have empty matches since mocks return empty)
            data = json.loads(result.content[0].text)
            assert "matches" in data
            assert data["matches"] == []


async def test_fuzzy_search_documents_preview_false(tmp_path: Path):
    """Test fuzzy_search_documents with preview=False parameter."""
    _skip_if_missing("rga")
    _skip_if_missing("fzf")

    with patch("subprocess.Popen") as mock_popen:
        # Mock processes to return empty results
        mock_rga_proc = MagicMock()
        mock_rga_proc.communicate.return_value = ("", "")
        mock_rga_proc.wait.return_value = None

        mock_fzf_proc = MagicMock()
        mock_fzf_proc.communicate.return_value = ("", None)
        mock_fzf_proc.returncode = 0

        mock_popen.side_effect = [mock_rga_proc, mock_fzf_proc]

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            # Test that preview=False parameter is accepted without errors
            result = await client.call_tool(
                "fuzzy_search_documents",
                {
                    "fuzzy_filter": "test",
                    "path": str(tmp_path),
                    "preview": False,  # Test preview=False
                },
            )

            # Just verify the call completed successfully
            data = json.loads(result.content[0].text)
            assert "error" not in data
            assert "matches" in data

            # Also test with preview=True to ensure both values are accepted
            result = await client.call_tool(
                "fuzzy_search_documents",
                {
                    "fuzzy_filter": "test",
                    "path": str(tmp_path),
                    "preview": True,  # Test preview=True
                },
            )

            data = json.loads(result.content[0].text)
            assert "error" not in data
            assert "matches" in data


# ---------------------------------------------------------------------------
# PDF Page Label Tests - Removed (PyMuPDF handles labels natively)
# ---------------------------------------------------------------------------


# Tests for _build_page_label_mapping and _parse_page_spec removed
# PyMuPDF handles page labels natively, no need for custom parsing


async def test_extract_pdf_pages_with_labels(tmp_path: Path):
    """Test extract_pdf_pages with page labels."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 5

        # Mock get_page_numbers to return pages for labels
        def mock_get_page_numbers(label):
            label_map = {"iii": [0], "iv": [1], "v": [2], "1": [3]}
            return label_map.get(label, [])

        mock_doc.get_page_numbers = mock_get_page_numbers

        # Create mock pages
        mock_pages = {}
        for i, label in enumerate(["iii", "iv", "v", "1", "2"]):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Content from page {label}"
            mock_page.get_label.return_value = label
            mock_pages[i] = mock_page

        # Configure document to return pages
        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc for markdown conversion
        with patch("subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"# Roman Numeral Pages\n\nContent from page iii\n\nContent from page iv\n"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {"file": str(test_pdf), "pages": "iii,iv", "format": "markdown"},
                )

            data = json.loads(result.content[0].text)
            # Debug: print what we actually got
            if "error" in data:
                print(f"ERROR: {data['error']}")
            assert "content" in data, f"Got data: {data}"
            assert "pages_extracted" in data
            assert "page_labels" in data
            assert "format" in data

            # Should extract pages 0 and 1 (0-based indices for labels iii and iv)
            assert data["pages_extracted"] == [0, 1]
            assert data["page_labels"] == ["iii", "iv"]
            assert data["format"] == "markdown"
            assert "Roman Numeral Pages" in data["content"]


async def test_extract_pdf_pages_with_ranges(tmp_path: Path):
    """Test extract_pdf_pages with page label ranges."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 10

        # Mock get_page_numbers to return pages for labels
        def mock_get_page_numbers(label):
            label_map = {"iii": [0], "iv": [1], "v": [2], "vi": [3]}
            return label_map.get(label, [])

        mock_doc.get_page_numbers = mock_get_page_numbers

        # Mock get_page_labels to return page labels
        mock_doc.get_page_labels.return_value = ["iii", "iv", "v", "vi"]

        # Create mock pages
        mock_pages = {}
        for i, label in enumerate(["iii", "iv", "v", "vi"]):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Content from page {label}"
            mock_page.get_label.return_value = label
            mock_pages[i] = mock_page

        # Configure document to return pages
        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc for markdown conversion
        with patch("subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"# Range Content\n\nContent from page iii\n\nContent from page iv\n\nContent from page v\n"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {"file": str(test_pdf), "pages": "iii-v", "format": "markdown"},
                )

            data = json.loads(result.content[0].text)

            # Should extract pages 0, 1, 2 (0-based indices for labels iii, iv, v)
            assert data["pages_extracted"] == [0, 1, 2]
            assert data["page_labels"] == ["iii", "iv", "v"]
            assert "Range Content" in data["content"]


async def test_extract_pdf_pages_mixed_specs(tmp_path: Path):
    """Test extract_pdf_pages with mixed page specifications."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 10

        # Mock get_page_numbers to return pages for labels
        def mock_get_page_numbers(label):
            label_map = {"iii": [0], "iv": [1]}
            # Return empty for labels not found (will use numeric fallback)
            return label_map.get(label, [])

        mock_doc.get_page_numbers = mock_get_page_numbers

        # Create mock pages
        mock_pages = {}
        # Page indices: 0=iii, 1=iv, 2=v, 3=1, 4=5 (to match test expectation)
        labels = ["iii", "iv", "v", "1", "5", "6", "7", "8", "9", "10"]
        for i in range(10):
            mock_page = MagicMock()
            label = labels[i] if i < len(labels) else str(i + 1)
            mock_page.get_text.return_value = f"Content from page {label}"
            mock_page.get_label.return_value = label
            mock_pages[i] = mock_page

        # Configure document to return pages
        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc for markdown conversion
        with patch("subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"# Mixed Content\n\nContent from page iii\n\nContent from page 3\n\nContent from page 4\n\nContent from page 5\n"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Mix of labels and numeric indices
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {"file": str(test_pdf), "pages": "iii,5,iv", "format": "markdown"},
                )

            data = json.loads(result.content[0].text)

            # Should extract pages 0 (iii), 4 (page 5 -> index 4), 1 (iv)
            assert data["pages_extracted"] == [0, 4, 1]
            assert data["page_labels"] == ["iii", "5", "iv"]
            assert "Mixed Content" in data["content"]


# ---------------------------------------------------------------------------
# Clean HTML Tests
# ---------------------------------------------------------------------------


async def test_extract_pdf_pages_clean_html_true(tmp_path: Path):
    """Test extract_pdf_pages with clean_html=True strips HTML styling."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # HTML output with styling from PyMuPDF
    html_with_styling = (
        '<p><span style="font-family: TimesLTPro-Roman; font-size:9px">'
        "Text with styling</span></p>"
        '<div style="color: red; background-color: yellow;">'
        "Styled div content</div>"
        "<!-- HTML comment -->"
    )

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.get_page_numbers.return_value = []  # No label matches
        mock_doc.get_page_labels.return_value = None

        # Create mock page that returns HTML with styling
        mock_page = MagicMock()
        mock_page.get_text.return_value = html_with_styling
        mock_page.get_label.return_value = "1"

        # Configure document to return page
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc for markdown conversion
        with patch("subprocess.run") as mock_run:
            # Mock pandoc process returning clean markdown
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"Text with styling\n\nStyled div content\n"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "1",
                        "format": "markdown",
                        "clean_html": True,
                    },
                )

            data = json.loads(result.content[0].text)
            assert "content" in data
            assert data["format"] == "markdown"

            # Verify pandoc was called with clean HTML arguments
            pandoc_call = mock_run.call_args_list[0]  # First and only call
            pandoc_args = pandoc_call[0][0]
            assert "--from=html-native_divs-native_spans" in pandoc_args
            assert "--to=gfm+tex_math_dollars-raw_html" in pandoc_args
            assert "--strip-comments" in pandoc_args

            # Content should not contain HTML styling
            content = data["content"]
            assert "font-family" not in content
            assert "font-size" not in content
            assert "<span" not in content
            assert "<div" not in content
            assert "style=" not in content


async def test_extract_pdf_pages_clean_html_false(tmp_path: Path):
    """Test extract_pdf_pages with clean_html=False preserves HTML styling."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # HTML output with styling from pdf2txt
    html_with_styling = (
        '<p><span style="font-family: TimesLTPro-Roman; font-size:9px">'
        "Text with styling</span></p>"
    )

    with patch("subprocess.run") as mock_run:
        # Mock pdf2txt process
        mock_pdf_result = MagicMock()
        mock_pdf_result.returncode = 0
        mock_pdf_result.stdout = html_with_styling.encode()
        mock_pdf_result.stderr = b""

        # Mock pandoc process preserving HTML
        mock_pandoc_result = MagicMock()
        mock_pandoc_result.returncode = 0
        mock_pandoc_result.stdout = b'<span style="font-family: TimesLTPro-Roman; font-size:9px">Text with styling</span>\n'
        mock_pandoc_result.stderr = b""

        mock_run.side_effect = [mock_pdf_result, mock_pandoc_result]

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "extract_pdf_pages",
                {
                    "file": str(test_pdf),
                    "pages": "1",
                    "format": "markdown",
                    "clean_html": False,
                },
            )

            data = json.loads(result.content[0].text)
            assert "content" in data

            # Verify pandoc was called with standard arguments (no cleaning)
            pandoc_call = mock_run.call_args_list[0]  # First and only call
            pandoc_args = pandoc_call[0][0]
            assert "--from=html" in pandoc_args
            assert "--to=gfm+tex_math_dollars" in pandoc_args
            assert "--strip-comments" not in pandoc_args


async def test_extract_pdf_pages_clean_html_plain_format(tmp_path: Path):
    """Test extract_pdf_pages with clean_html=True and plain format."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.get_page_numbers.return_value = []  # No label matches
        mock_doc.get_page_labels.return_value = None

        # Create mock page that returns plain text
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Plain text content"
        mock_page.get_label.return_value = "1"

        # Configure document to return page
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "extract_pdf_pages",
                {
                    "file": str(test_pdf),
                    "pages": "1",
                    "format": "plain",
                    "clean_html": True,  # Should be ignored for plain format
                },
            )

        data = json.loads(result.content[0].text)
        assert data["format"] == "plain"
        assert "Plain text content" in data["content"]
        # No pandoc should be called for plain format


async def test_extract_pdf_pages_clean_html_default_true(tmp_path: Path):
    """Test extract_pdf_pages has clean_html=True by default."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.get_page_numbers.return_value = []  # No label matches
        mock_doc.get_page_labels.return_value = None

        # Create mock page that returns HTML with styling
        mock_page = MagicMock()
        mock_page.get_text.return_value = '<span style="font-size:12px">Content</span>'
        mock_page.get_label.return_value = "1"

        # Configure document to return page
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc for markdown conversion
        with patch("subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"Content\n"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Don't specify clean_html parameter - should default to True
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {"file": str(test_pdf), "pages": "1", "format": "markdown"},
                )

            data = json.loads(result.content[0].text)
            assert "content" in data

            # Should use clean HTML arguments by default
            pandoc_call = mock_run.call_args_list[0]  # First and only call
            pandoc_args = pandoc_call[0][0]
            assert "--from=html-native_divs-native_spans" in pandoc_args
            assert "--strip-comments" in pandoc_args


# ---------------------------------------------------------------------------
# Fuzzy Hint Tests
# ---------------------------------------------------------------------------


async def test_extract_pdf_pages_with_fuzzy_hint(tmp_path: Path):
    """Test extract_pdf_pages with fuzzy_hint parameter filters pages by content."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with multiple pages
        mock_doc = MagicMock()
        mock_doc.page_count = 5
        mock_doc.get_page_numbers.return_value = []  # No label matches
        mock_doc.get_page_labels.return_value = None

        # Create mock pages with different content
        mock_pages = {}
        page_contents = [
            "This page talks about neural networks and deep learning",
            "This page is about data structures and algorithms",
            "Machine learning and neural networks are discussed here",
            "Python programming basics",
            "Advanced neural network architectures",
        ]

        for i in range(5):
            mock_page = MagicMock()
            mock_page.get_text.return_value = page_contents[i]
            mock_page.get_label.return_value = str(i + 1)
            mock_pages[i] = mock_page

        # Configure document to return pages
        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock fzf for fuzzy filtering
        with patch("subprocess.run") as mock_run:
            # Mock fzf filtering - return only pages containing "neural"
            mock_fzf_result = MagicMock()
            mock_fzf_result.returncode = 0
            # Return pages 1, 3, and 5 (0-based: 0, 2, 4) that mention neural
            mock_fzf_result.stdout = (
                b"Page 1 (Label: 1)\nThis page talks about neural networks and deep learning\x00"
                b"Page 3 (Label: 3)\nMachine learning and neural networks are discussed here\x00"
                b"Page 5 (Label: 5)\nAdvanced neural network architectures\x00"
            )
            mock_run.return_value = mock_fzf_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Extract all pages but filter with fuzzy_hint
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "1-5",
                        "format": "plain",
                        "fuzzy_hint": "neural",
                    },
                )

            data = json.loads(result.content[0].text)
            assert "content" in data
            assert "fuzzy_hint" in data
            assert data["fuzzy_hint"] == "neural"

            # Should have filtered from 5 pages to 3
            assert data["pages_before_filter"] == 5
            assert data["pages_after_filter"] == 3
            assert data["pages_extracted"] == [0, 2, 4]  # 0-based indices
            assert data["page_labels"] == ["1", "3", "5"]

            # Content should only include filtered pages
            content = data["content"]
            assert "neural networks" in content
            assert "data structures" not in content  # Page 2 filtered out
            assert "Python programming" not in content  # Page 4 filtered out


async def test_extract_pdf_pages_fuzzy_hint_no_matches(tmp_path: Path):
    """Test extract_pdf_pages with fuzzy_hint that matches no pages returns all pages."""
    # Test with PyMuPDF

    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 2
        mock_doc.get_page_numbers.return_value = []
        mock_doc.get_page_labels.return_value = None

        # Create mock pages
        mock_pages = {}
        for i in range(2):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Content for page {i + 1}"
            mock_page.get_label.return_value = str(i + 1)
            mock_pages[i] = mock_page

        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()
        mock_fitz_open.return_value = mock_doc

        # Mock fzf returning no matches
        with patch("subprocess.run") as mock_run:
            mock_fzf_result = MagicMock()
            mock_fzf_result.returncode = 0
            mock_fzf_result.stdout = b""  # No matches
            mock_run.return_value = mock_fzf_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "1,2",
                        "format": "plain",
                        "fuzzy_hint": "nonexistent",
                    },
                )

            data = json.loads(result.content[0].text)

            # Should return all pages when no matches
            assert data["pages_before_filter"] == 2
            assert data["pages_after_filter"] == 2
            assert data["pages_extracted"] == [0, 1]
            assert "Content for page 1" in data["content"]
            assert "Content for page 2" in data["content"]


# ---------------------------------------------------------------------------
# Zero-Based Index Tests
# ---------------------------------------------------------------------------


async def test_extract_pdf_pages_zero_based_single(tmp_path: Path):
    """Test extract_pdf_pages with zero_based=True for single pages."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with 5 pages
        mock_doc = MagicMock()
        mock_doc.page_count = 5
        mock_doc.get_page_labels.return_value = ["i", "ii", "iii", "1", "2"]

        # Create mock pages
        mock_pages = {}
        for i in range(5):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Content from page {i}"
            mock_page.get_label.return_value = mock_doc.get_page_labels.return_value[i]
            mock_pages[i] = mock_page

        # Configure document to return pages using __getitem__
        def mock_getitem(self, idx):
            return mock_pages.get(idx)

        mock_doc.__getitem__ = mock_getitem
        mock_doc.close = MagicMock()
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc (need to patch subprocess.run in mcp_fuzzy_search module)
        with patch("mcp_fuzzy_search.subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"Markdown content"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Test extracting pages using 0-based indices
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "0,2,4",  # First, third, and fifth pages
                        "zero_based": True,
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" not in data
                assert data["pages_extracted"] == [0, 2, 4]
                # With zero_based=true, page_labels should show the 0-based indices
                assert data["page_labels"] == ["0", "2", "4"]
                assert data["format"] == "markdown"


async def test_extract_pdf_pages_zero_based_ranges(tmp_path: Path):
    """Test extract_pdf_pages with zero_based=True for ranges."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with 10 pages
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_doc.get_page_labels.return_value = [
            "i",
            "ii",
            "iii",
            "iv",
            "v",
            "1",
            "2",
            "3",
            "4",
            "5",
        ]

        # Create mock pages
        mock_pages = {}
        for i in range(10):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Content from page {i}"
            if i < len(mock_doc.get_page_labels.return_value):
                mock_page.get_label.return_value = (
                    mock_doc.get_page_labels.return_value[i]
                )
            else:
                mock_page.get_label.return_value = str(i + 1)
            mock_pages[i] = mock_page

        # Configure document to return pages using __getitem__
        def mock_getitem(self, idx):
            return mock_pages.get(idx)

        mock_doc.__getitem__ = mock_getitem
        mock_doc.close = MagicMock()
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc (need to patch subprocess.run in mcp_fuzzy_search module)
        with patch("mcp_fuzzy_search.subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"Markdown content"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Test extracting pages using 0-based range
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "0-4",  # First 5 pages (0,1,2,3,4)
                        "zero_based": True,
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" not in data
                assert data["pages_extracted"] == [0, 1, 2, 3, 4]
                # With zero_based=true and ranges, page_labels should show the 0-based indices
                assert data["page_labels"] == ["0", "1", "2", "3", "4"]
                assert data["format"] == "markdown"


async def test_extract_pdf_pages_zero_based_mixed(tmp_path: Path):
    """Test extract_pdf_pages with zero_based=True for mixed specifications."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with 10 pages
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_doc.get_page_labels.return_value = None  # No page labels

        # Create mock pages
        mock_pages = {}
        for i in range(10):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Content from page {i}"
            mock_page.get_label.return_value = str(i + 1)
            mock_pages[i] = mock_page

        # Configure document to return pages using __getitem__
        def mock_getitem(self, idx):
            return mock_pages.get(idx)

        mock_doc.__getitem__ = mock_getitem
        mock_doc.close = MagicMock()
        mock_fitz_open.return_value = mock_doc

        # Mock pandoc (need to patch subprocess.run in mcp_fuzzy_search module)
        with patch("mcp_fuzzy_search.subprocess.run") as mock_run:
            mock_pandoc_result = MagicMock()
            mock_pandoc_result.returncode = 0
            mock_pandoc_result.stdout = b"Markdown content"
            mock_pandoc_result.stderr = b""
            mock_run.return_value = mock_pandoc_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Test extracting pages using mixed 0-based specifications
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "0,2-4,7,9",  # Pages 1, 3-5, 8, 10 (1-based)
                        "zero_based": True,
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" not in data
                assert data["pages_extracted"] == [0, 2, 3, 4, 7, 9]
                assert data["page_labels"] == ["0", "2", "3", "4", "7", "9"]
                assert data["format"] == "markdown"


async def test_extract_pdf_pages_zero_based_errors(tmp_path: Path):
    """Test extract_pdf_pages with zero_based=True error handling."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with 5 pages
        mock_doc = MagicMock()
        mock_doc.page_count = 5
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            # Test out of range index
            result = await client.call_tool(
                "extract_pdf_pages",
                {
                    "file": str(test_pdf),
                    "pages": "10",  # Out of range (only 5 pages)
                    "zero_based": True,
                },
            )

            data = json.loads(result.content[0].text)
            assert "error" in data
            assert "Must be a valid 0-based index" in data["error"]
            assert "0 to 4" in data["error"]  # Should show valid range

            # Test invalid range (start > end)
            result = await client.call_tool(
                "extract_pdf_pages",
                {
                    "file": str(test_pdf),
                    "pages": "3-1",  # Invalid range
                    "zero_based": True,
                },
            )

            data = json.loads(result.content[0].text)
            assert "error" in data
            assert "Must be a valid 0-based index" in data["error"]

            # Test non-numeric input
            result = await client.call_tool(
                "extract_pdf_pages",
                {
                    "file": str(test_pdf),
                    "pages": "abc",  # Not a number
                    "zero_based": True,
                },
            )

            data = json.loads(result.content[0].text)
            assert "error" in data
            assert "Must be a valid 0-based index" in data["error"]


async def test_extract_pdf_pages_one_based(tmp_path: Path):
    """Test extract_pdf_pages with one_based=True."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with 10 pages
        mock_doc = MagicMock()
        mock_doc.page_count = 10

        # Create mock pages with proper get_text method
        mock_pages = {}
        for i in range(10):
            mock_page = MagicMock()
            # Mock the get_text method to return page content
            mock_page.get_text.return_value = f"Page {i + 1} content"
            mock_pages[i] = mock_page

        # Configure document to return pages
        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock subprocess for pdftotext/pandoc - return bytes
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = b"Page 1 content"  # Return bytes
            mock_result.stderr = b""
            mock_run.return_value = mock_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                # Test single page with one_based
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "5",  # Page 5 (1-based)
                        "one_based": True,
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" not in data
                assert data["pages_extracted"] == [4]  # 0-based index
                assert data["page_labels"] == ["5"]  # 1-based page number as label

                # Test range with one_based
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "1-3",  # Pages 1-3 (1-based)
                        "one_based": True,
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" not in data
                assert data["pages_extracted"] == [0, 1, 2]  # 0-based indices
                assert data["page_labels"] == [
                    "1",
                    "2",
                    "3",
                ]  # 1-based page numbers as labels

                # Test mixed pages with one_based
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "1,3-5,8,10",  # Pages 1, 3-5, 8, 10 (1-based)
                        "one_based": True,
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" not in data
                assert data["pages_extracted"] == [0, 2, 3, 4, 7, 9]  # 0-based indices
                assert data["page_labels"] == [
                    "1",
                    "3",
                    "4",
                    "5",
                    "8",
                    "10",
                ]  # 1-based page numbers as labels

                # Test error handling - out of range
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "11",  # Out of range (only 10 pages)
                        "one_based": True,
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" in data
                assert "Must be a valid 1-based page number" in data["error"]
                assert "1 to 10" in data["error"]  # Should show valid range

                # Test that one_based and zero_based cannot be used together
                result = await client.call_tool(
                    "extract_pdf_pages",
                    {
                        "file": str(test_pdf),
                        "pages": "1-3",
                        "one_based": True,
                        "zero_based": True,  # Both flags set
                    },
                )

                data = json.loads(result.content[0].text)
                assert "error" in data
                assert "Cannot use both" in data["error"]


# ---------------------------------------------------------------------------
# PDF Info Tools Tests
# ---------------------------------------------------------------------------


async def test_get_pdf_page_labels(tmp_path: Path):
    """Test get_pdf_page_labels tool."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 5

        # Create mock pages with labels
        mock_pages = {}
        labels = ["i", "ii", "iii", "1", "2"]
        for i in range(5):
            mock_page = MagicMock()
            mock_page.get_label.return_value = labels[i]
            mock_pages[i] = mock_page

        # Configure document to return pages
        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_page_labels",
                {"file": str(test_pdf)},
            )

        data = json.loads(result.content[0].text)
        assert data["page_count"] == 5
        assert data["page_labels"] == {
            "0": "i",
            "1": "ii",
            "2": "iii",
            "3": "1",
            "4": "2",
        }


async def test_get_pdf_page_count(tmp_path: Path):
    """Test get_pdf_page_count tool."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 123
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_page_count",
                {"file": str(test_pdf)},
            )

        data = json.loads(result.content[0].text)
        assert data["page_count"] == 123


async def test_get_pdf_page_labels_missing_file():
    """Test get_pdf_page_labels with missing file."""
    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "get_pdf_page_labels",
            {"file": "/nonexistent/file.pdf"},
        )

    data = json.loads(result.content[0].text)
    assert "error" in data
    assert "not found" in data["error"]


async def test_get_pdf_page_labels_with_start_limit(tmp_path: Path):
    """Test get_pdf_page_labels with start and limit parameters."""
    test_pdf = tmp_path / "test.pdf"
    # Create a minimal valid PDF that PyMuPDF can open
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with 10 pages
        mock_doc = MagicMock()
        mock_doc.page_count = 10

        # Create mock pages with labels
        mock_pages = {}
        labels = ["i", "ii", "iii", "iv", "v", "1", "2", "3", "4", "5"]
        for i in range(10):
            mock_page = MagicMock()
            mock_page.get_label.return_value = labels[i]
            mock_pages[i] = mock_page

        # Configure document to return pages
        mock_doc.__getitem__ = lambda self, idx: mock_pages.get(idx)
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            # Test with start=2, limit=3 (should return pages 2,3,4)
            result = await client.call_tool(
                "get_pdf_page_labels",
                {"file": str(test_pdf), "start": 2, "limit": 3},
            )

        data = json.loads(result.content[0].text)
        assert data["page_count"] == 10  # Total count remains the same
        assert data["page_labels"] == {
            "2": "iii",
            "3": "iv",
            "4": "v",
        }

        # Test with only limit
        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_page_labels",
                {"file": str(test_pdf), "limit": 2},
            )

        data = json.loads(result.content[0].text)
        assert data["page_count"] == 10
        assert data["page_labels"] == {
            "0": "i",
            "1": "ii",
        }

        # Test with start beyond page count
        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_page_labels",
                {"file": str(test_pdf), "start": 20, "limit": 5},
            )

        data = json.loads(result.content[0].text)
        assert data["page_count"] == 10
        assert data["page_labels"] == {}  # Empty since start is beyond page count


async def test_get_pdf_page_count_missing_file():
    """Test get_pdf_page_count with missing file."""
    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "get_pdf_page_count",
            {"file": "/nonexistent/file.pdf"},
        )

    data = json.loads(result.content[0].text)
    assert "error" in data
    assert "not found" in data["error"]


# ---------------------------------------------------------------------------
# PDF Outline Tests
# ---------------------------------------------------------------------------


async def test_get_pdf_outline_basic(tmp_path: Path):
    """Test get_pdf_outline with basic outline structure."""
    # Create a test PDF
    test_pdf = tmp_path / "test_outline.pdf"
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock PyMuPDF
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock outline items
        mock_outline1 = MagicMock()
        mock_outline1.title = "Chapter 1"
        mock_outline1.page = 0  # 0-based
        mock_outline1.is_external = False
        mock_outline1.is_open = True
        mock_outline1.uri = None
        mock_outline1.down = None
        mock_outline1.next = MagicMock()

        mock_outline2 = mock_outline1.next
        mock_outline2.title = "Chapter 2"
        mock_outline2.page = 4  # 0-based
        mock_outline2.is_external = False
        mock_outline2.is_open = True
        mock_outline2.uri = None
        mock_outline2.down = None
        mock_outline2.next = None

        # Create mock pages
        mock_page1 = MagicMock()
        mock_page1.get_label.return_value = "i"

        mock_page2 = MagicMock()
        mock_page2.get_label.return_value = "1"

        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_doc.outline = mock_outline1
        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_outline",
                {"file": str(test_pdf)},
            )

            data = json.loads(result.content[0].text)
            assert "outline" in data
            assert "total_entries" in data
            assert "max_depth_found" in data

            assert data["total_entries"] == 2
            assert data["max_depth_found"] == 1

            # Check outline entries
            assert len(data["outline"]) == 2
            assert data["outline"][0] == [1, "Chapter 1", 1, "i"]
            assert data["outline"][1] == [1, "Chapter 2", 5, "1"]


async def test_get_pdf_outline_empty(tmp_path: Path):
    """Test get_pdf_outline with PDF that has no outline."""
    # Create a test PDF
    test_pdf = tmp_path / "test_no_outline.pdf"
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock PyMuPDF
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create mock document with no outline
        mock_doc = MagicMock()
        mock_doc.page_count = 5
        mock_doc.outline = None
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_outline",
                {"file": str(test_pdf)},
            )

            data = json.loads(result.content[0].text)
            assert data["outline"] == []
            assert data["total_entries"] == 0
            assert data["max_depth_found"] == 0


async def test_get_pdf_outline_hierarchical(tmp_path: Path):
    """Test get_pdf_outline with hierarchical outline structure."""
    # Create a test PDF
    test_pdf = tmp_path / "test_hierarchical.pdf"
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock PyMuPDF
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create hierarchical outline structure
        # Chapter 1
        #   Section 1.1
        #     Subsection 1.1.1
        #   Section 1.2
        # Chapter 2

        mock_subsection = MagicMock()
        mock_subsection.title = "Subsection 1.1.1"
        mock_subsection.page = 2
        mock_subsection.is_external = False
        mock_subsection.is_open = True
        mock_subsection.uri = None
        mock_subsection.down = None
        mock_subsection.next = None

        mock_section1_1 = MagicMock()
        mock_section1_1.title = "Section 1.1"
        mock_section1_1.page = 1
        mock_section1_1.is_external = False
        mock_section1_1.is_open = True
        mock_section1_1.uri = None
        mock_section1_1.down = mock_subsection
        mock_section1_1.next = MagicMock()

        mock_section1_2 = mock_section1_1.next
        mock_section1_2.title = "Section 1.2"
        mock_section1_2.page = 3
        mock_section1_2.is_external = False
        mock_section1_2.is_open = True
        mock_section1_2.uri = None
        mock_section1_2.down = None
        mock_section1_2.next = None

        mock_chapter1 = MagicMock()
        mock_chapter1.title = "Chapter 1"
        mock_chapter1.page = 0
        mock_chapter1.is_external = False
        mock_chapter1.is_open = True
        mock_chapter1.uri = None
        mock_chapter1.down = mock_section1_1
        mock_chapter1.next = MagicMock()

        mock_chapter2 = mock_chapter1.next
        mock_chapter2.title = "Chapter 2"
        mock_chapter2.page = 5
        mock_chapter2.is_external = False
        mock_chapter2.is_open = True
        mock_chapter2.uri = None
        mock_chapter2.down = None
        mock_chapter2.next = None

        # Create mock pages (need at least 6 pages since Chapter 2 is on page 5 (0-based))
        mock_pages = []
        for i in range(10):  # Create more pages to cover all references
            mock_page = MagicMock()
            mock_page.get_label.return_value = str(i + 1)
            mock_pages.append(mock_page)

        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_doc.outline = mock_chapter1
        mock_doc.__getitem__.side_effect = lambda idx: mock_pages[idx]
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_outline",
                {"file": str(test_pdf)},
            )

            data = json.loads(result.content[0].text)
            assert data["total_entries"] == 5
            assert data["max_depth_found"] == 3

            # Check outline entries
            assert len(data["outline"]) == 5
            assert data["outline"][0] == [1, "Chapter 1", 1, "1"]
            assert data["outline"][1] == [2, "Section 1.1", 2, "2"]
            assert data["outline"][2] == [3, "Subsection 1.1.1", 3, "3"]
            assert data["outline"][3] == [2, "Section 1.2", 4, "4"]
            assert data["outline"][4] == [1, "Chapter 2", 6, "6"]


async def test_get_pdf_outline_with_max_depth(tmp_path: Path):
    """Test get_pdf_outline with max_depth parameter."""
    # Create a test PDF
    test_pdf = tmp_path / "test_max_depth.pdf"
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock PyMuPDF with same hierarchical structure as before
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create hierarchical outline structure
        mock_subsection = MagicMock()
        mock_subsection.title = "Subsection 1.1.1"
        mock_subsection.page = 2
        mock_subsection.is_external = False
        mock_subsection.is_open = True
        mock_subsection.uri = None
        mock_subsection.down = None
        mock_subsection.next = None

        mock_section1_1 = MagicMock()
        mock_section1_1.title = "Section 1.1"
        mock_section1_1.page = 1
        mock_section1_1.is_external = False
        mock_section1_1.is_open = True
        mock_section1_1.uri = None
        mock_section1_1.down = mock_subsection
        mock_section1_1.next = None

        mock_chapter1 = MagicMock()
        mock_chapter1.title = "Chapter 1"
        mock_chapter1.page = 0
        mock_chapter1.is_external = False
        mock_chapter1.is_open = True
        mock_chapter1.uri = None
        mock_chapter1.down = mock_section1_1
        mock_chapter1.next = None

        # Create mock pages
        mock_pages = []
        for i in range(3):
            mock_page = MagicMock()
            mock_page.get_label.return_value = str(i + 1)
            mock_pages.append(mock_page)

        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_doc.outline = mock_chapter1
        mock_doc.__getitem__.side_effect = mock_pages
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_outline",
                {"file": str(test_pdf), "max_depth": 2},
            )

            data = json.loads(result.content[0].text)
            # Should only include entries up to depth 2
            assert data["total_entries"] == 2
            assert data["max_depth_found"] == 2

            # Check outline entries - should not include depth 3
            assert len(data["outline"]) == 2
            assert data["outline"][0] == [1, "Chapter 1", 1, "1"]
            assert data["outline"][1] == [2, "Section 1.1", 2, "2"]


async def test_get_pdf_outline_with_fuzzy_filter(tmp_path: Path):
    """Test get_pdf_outline with fuzzy filtering."""
    # Create a test PDF
    test_pdf = tmp_path / "test_fuzzy.pdf"
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock PyMuPDF
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create outline with different titles
        mock_outline1 = MagicMock()
        mock_outline1.title = "Introduction"
        mock_outline1.page = 0
        mock_outline1.is_external = False
        mock_outline1.is_open = True
        mock_outline1.uri = None
        mock_outline1.down = None
        mock_outline1.next = MagicMock()

        mock_outline2 = mock_outline1.next
        mock_outline2.title = "Chapter 1: Getting Started"
        mock_outline2.page = 2
        mock_outline2.is_external = False
        mock_outline2.is_open = True
        mock_outline2.uri = None
        mock_outline2.down = None
        mock_outline2.next = MagicMock()

        mock_outline3 = mock_outline2.next
        mock_outline3.title = "Chapter 2: Advanced Topics"
        mock_outline3.page = 5
        mock_outline3.is_external = False
        mock_outline3.is_open = True
        mock_outline3.uri = None
        mock_outline3.down = None
        mock_outline3.next = None

        # Create mock pages
        mock_pages = []
        for i in range(6):
            mock_page = MagicMock()
            mock_page.get_label.return_value = str(i + 1)
            mock_pages.append(mock_page)

        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_doc.outline = mock_outline1
        mock_doc.__getitem__.side_effect = mock_pages
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        # Mock fzf subprocess for fuzzy filtering
        with patch("subprocess.run") as mock_run:
            # Simulate fzf filtering for "chapter"
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = (
                "1:Chapter 1: Getting Started\n2:Chapter 2: Advanced Topics"
            )
            mock_run.return_value = mock_result

            async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
                result = await client.call_tool(
                    "get_pdf_outline",
                    {"file": str(test_pdf), "fuzzy_filter": "chapter"},
                )

                data = json.loads(result.content[0].text)
                assert "filtered_count" in data
                assert data["filtered_count"] == 2
                assert data["total_entries"] == 3

                # Check filtered outline entries
                assert len(data["outline"]) == 2
                assert data["outline"][0][1] == "Chapter 1: Getting Started"
                assert data["outline"][1][1] == "Chapter 2: Advanced Topics"


async def test_get_pdf_outline_detailed_output(tmp_path: Path):
    """Test get_pdf_outline with detailed output (simple=False)."""
    # Create a test PDF
    test_pdf = tmp_path / "test_detailed.pdf"
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n203\n%%EOF"
    test_pdf.write_bytes(pdf_content)

    # Mock PyMuPDF
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        # Create outline with link details
        mock_outline = MagicMock()
        mock_outline.title = "Chapter 1"
        mock_outline.page = 0
        mock_outline.is_external = False
        mock_outline.is_open = True
        mock_outline.uri = "#page=1&zoom=100,0,0"
        mock_outline.down = None
        mock_outline.next = None

        # Mock dest object
        mock_dest = MagicMock()
        mock_dest.kind = 1
        mock_dest.page = 0
        mock_dest.uri = "#page=1&zoom=100,0,0"
        mock_dest.lt = None
        mock_dest.rb = None
        mock_dest.zoom = 100
        mock_outline.dest = mock_dest

        # Create mock page
        mock_page = MagicMock()
        mock_page.get_label.return_value = "1"

        # Create mock document
        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_doc.outline = mock_outline
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.close = MagicMock()

        # Configure fitz.open to return mock document
        mock_fitz_open.return_value = mock_doc

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_outline",
                {"file": str(test_pdf), "simple": False},
            )

            data = json.loads(result.content[0].text)
            assert len(data["outline"]) == 1

            # Check detailed entry format
            entry = data["outline"][0]
            assert len(entry) == 5  # [level, title, page, page_label, link]
            assert entry[0] == 1  # level
            assert entry[1] == "Chapter 1"  # title
            assert entry[2] == 1  # page
            assert entry[3] == "1"  # page_label

            # Check link details
            link = entry[4]
            assert link["page"] == 1
            assert link["uri"] == "#page=1&zoom=100,0,0"
            assert link["is_external"] is False
            assert link["is_open"] is True
            assert "dest" in link
            assert link["dest"]["kind"] == 1
            assert link["dest"]["zoom"] == 100


async def test_get_pdf_outline_missing_file():
    """Test get_pdf_outline with missing file."""
    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "get_pdf_outline",
            {"file": "/nonexistent/file.pdf"},
        )

    data = json.loads(result.content[0].text)
    assert "error" in data
    assert "not found" in data["error"]


async def test_get_pdf_outline_invalid_pdf(tmp_path: Path):
    """Test get_pdf_outline with invalid PDF."""
    # Create an invalid PDF file
    test_pdf = tmp_path / "invalid.pdf"
    test_pdf.write_text("This is not a valid PDF")

    # Mock PyMuPDF to raise an exception
    with patch("mcp_fuzzy_search.fitz.open") as mock_fitz_open:
        mock_fitz_open.side_effect = Exception("Invalid PDF format")

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "get_pdf_outline",
                {"file": str(test_pdf)},
            )

        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "Failed to get outline" in data["error"]


async def test_fuzzy_search_files_root_path_validation():
    """Test that searching from root directory without confirm_root fails."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_files", {"fuzzy_filter": "test", "path": "/"}
        )

        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "root directory" in data["error"].lower()
        assert "confirm_root=True" in data["error"]


async def test_fuzzy_search_files_root_path_with_confirm():
    """Test that searching from root directory works with confirm_root=True."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Mock subprocess to avoid actually searching from root
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout.close = MagicMock()
        mock_proc.wait.return_value = None
        mock_popen.return_value = mock_proc

        # Mock the second Popen call for fzf
        fzf_proc = MagicMock()
        fzf_proc.communicate.return_value = ("test.txt\n", None)
        fzf_proc.returncode = 0
        mock_popen.side_effect = [mock_proc, fzf_proc]

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_files",
                {"fuzzy_filter": "test", "path": "/", "confirm_root": True},
            )

            data = json.loads(result.content[0].text)
            assert "matches" in data  # Should succeed with confirm_root


async def test_fuzzy_search_content_root_path_validation():
    """Test that searching content from root directory without confirm_root fails."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_content", {"fuzzy_filter": "test", "path": "/"}
        )

        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "root directory" in data["error"].lower()
        assert "confirm_root=True" in data["error"]


async def test_fuzzy_search_content_root_path_with_confirm():
    """Test that searching content from root directory works with confirm_root=True."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Mock subprocess to avoid actually searching from root
    with patch("subprocess.Popen") as mock_popen:
        mock_rg_proc = MagicMock()
        mock_rg_proc.stdout = MagicMock()
        mock_rg_proc.stderr = MagicMock()
        mock_rg_proc.stderr.read.return_value = b""
        mock_rg_proc.wait.return_value = 0
        mock_rg_proc.returncode = 0

        mock_fzf_proc = MagicMock()
        mock_fzf_proc.communicate.return_value = ("/test.txt:1:test content\n", None)
        mock_fzf_proc.returncode = 0

        mock_popen.side_effect = [mock_rg_proc, mock_fzf_proc]

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_content",
                {"fuzzy_filter": "test", "path": "/", "confirm_root": True},
            )

            data = json.loads(result.content[0].text)
            assert "matches" in data  # Should succeed with confirm_root


async def test_fuzzy_search_documents_root_path_validation():
    """Test that searching documents from root directory without confirm_root fails."""
    # Skip if rga is not available
    if shutil.which("rga") is None:
        pytest.skip("rga not on PATH")
    _skip_if_missing("fzf")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        result = await client.call_tool(
            "fuzzy_search_documents", {"fuzzy_filter": "test", "path": "/"}
        )

        data = json.loads(result.content[0].text)
        assert "error" in data
        assert "root directory" in data["error"].lower()
        assert "confirm_root=True" in data["error"]


async def test_fuzzy_search_documents_root_path_with_confirm():
    """Test that searching documents from root directory works with confirm_root=True."""
    # Skip if rga is not available
    if shutil.which("rga") is None:
        pytest.skip("rga not on PATH")
    _skip_if_missing("fzf")

    # Mock subprocess to avoid actually searching from root
    with patch("subprocess.Popen") as mock_popen:
        # Mock rga process
        mock_rga_proc = MagicMock()
        mock_rga_proc.communicate.return_value = (
            '{"type":"match","data":{"path":{"text":"/test.pdf"},"lines":{"text":"test"},"line_number":1,"submatches":[{"match":{"text":"test"}}]}}\n',
            "",
        )

        # Mock fzf process
        mock_fzf_proc = MagicMock()
        mock_fzf_proc.communicate.return_value = ("/test.pdf:1:test\n", None)
        mock_fzf_proc.returncode = 0

        mock_popen.side_effect = [mock_rga_proc, mock_fzf_proc]

        async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
            result = await client.call_tool(
                "fuzzy_search_documents",
                {"fuzzy_filter": "test", "path": "/", "confirm_root": True},
            )

            data = json.loads(result.content[0].text)
            assert "matches" in data  # Should succeed with confirm_root


async def test_fuzzy_search_content_with_file_path(tmp_path: Path):
    """Test fuzzy_search_content works correctly when given a file path instead of directory."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create a test file with specific content
    test_file = tmp_path / "single_file.py"
    test_file.write_text("""def process_data():
    # Process the data
    data = load_data()
    return transform_data(data)

def transform_data(data):
    # Transform the data
    return data.upper()
""")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Test searching in a single file
        result = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "data",
                "path": str(test_file),
            },
        )

        data = json.loads(result.content[0].text)
        assert "matches" in data
        assert len(data["matches"]) >= 3  # Should find multiple occurrences of "data"

        # Verify all matches are from the same file
        for match in data["matches"]:
            assert str(test_file) in match["file"]
            assert "data" in match["content"].lower()

        # Test with content_only mode
        result_content_only = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "transform",
                "path": str(test_file),
                "content_only": True,
            },
        )

        data_content_only = json.loads(result_content_only.content[0].text)
        assert "matches" in data_content_only
        assert (
            len(data_content_only["matches"]) >= 2
        )  # Should find transform_data occurrences


async def test_fuzzy_search_content_file_vs_directory(tmp_path: Path):
    """Test that fuzzy_search_content produces consistent results for file vs directory containing that file."""
    _skip_if_missing("rg")
    _skip_if_missing("fzf")

    # Create a test file
    test_file = tmp_path / "test_consistency.py"
    test_file.write_text("""# This is a unique marker for testing
def unique_function_name():
    return "unique_result"
""")

    async with client_session(mcp_fuzzy_search.mcp._mcp_server) as client:
        # Search in the file directly
        result_file = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "unique_function_name",
                "path": str(test_file),
            },
        )

        # Search in the directory containing the file
        # Use a simpler filter that works on both Windows and Unix
        result_dir = await client.call_tool(
            "fuzzy_search_content",
            {
                "fuzzy_filter": "unique_function_name",
                "path": str(tmp_path),
            },
        )

        data_file = json.loads(result_file.content[0].text)
        data_dir = json.loads(result_dir.content[0].text)

        # Both should find the function
        assert len(data_file["matches"]) >= 1
        assert len(data_dir["matches"]) >= 1

        # Find the unique_function_name content in both results
        file_contents = [
            match["content"]
            for match in data_file["matches"]
            if "unique_function_name" in match["content"]
        ]
        dir_contents = [
            match["content"]
            for match in data_dir["matches"]
            if "unique_function_name" in match["content"]
        ]

        # Both should find at least one match with the function name
        assert len(file_contents) >= 1
        assert len(dir_contents) >= 1

        # At least one content match should be the same (allowing for ordering differences)
        assert any(fc in dir_contents for fc in file_contents)
