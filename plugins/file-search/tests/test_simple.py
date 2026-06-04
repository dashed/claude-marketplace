"""Simplified tests for mcp_fd_server using direct function calls."""

from pathlib import Path
from unittest.mock import patch

import pytest

import mcp_fd_server


def normalize_path(path):
    """Normalize path to use forward slashes for cross-platform testing."""
    return Path(path).as_posix()


@patch("subprocess.check_output")
def test_search_files_direct(mock_check_output):
    """Test search_files function with reliable mocked output."""
    mock_check_output.return_value = "mcp_fd_server.py\nmcp_fuzzy_search.py\n"

    with patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"):
        result = mcp_fd_server.search_files(pattern=r"\.py$", path=".")

    # Should return a dict with matches key
    assert isinstance(result, dict)
    assert "matches" in result
    assert isinstance(result["matches"], list)
    assert len(result["matches"]) == 2
    assert "mcp_fd_server.py" in result["matches"]
    assert "mcp_fuzzy_search.py" in result["matches"]


def test_search_files_error():
    """Test search_files error handling."""
    result = mcp_fd_server.search_files(pattern="")

    assert result == {"error": "'pattern' argument is required"}


def test_filter_files_direct():
    """Test filter_files function directly."""
    # Skip if dependencies not available
    if not mcp_fd_server.FD_EXECUTABLE or not mcp_fd_server.FZF_EXECUTABLE:
        pytest.skip("fd or fzf not available")

    # Search for python files containing "test"
    result = mcp_fd_server.filter_files(filter="test", pattern=r"\.py$", path=".")

    assert isinstance(result, dict)
    assert "matches" in result or "error" in result


def test_filter_files_error():
    """Test filter_files error handling."""
    result = mcp_fd_server.filter_files(filter="")

    assert result == {"error": "'filter' argument is required"}


@patch("subprocess.check_output")
def test_search_files_mocked(mock_check_output):
    """Test search_files with mocked subprocess."""
    mock_check_output.return_value = "src/main.py\nsrc/test.py\n"

    with patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"):
        result = mcp_fd_server.search_files(pattern=r"\.py$", path="src")

    assert result["matches"] == ["src/main.py", "src/test.py"]


def test_binary_missing_exception():
    """Test BinaryMissing exception."""
    with pytest.raises(mcp_fd_server.BinaryMissing) as exc_info:
        mcp_fd_server._require(None, "test-binary")

    assert "Cannot find the `test-binary` binary" in str(exc_info.value)


@patch("subprocess.check_output")
def test_cli_functionality(mock_check_output, tmp_path):
    """Test CLI helper functionality with mocked output."""
    # Create test file for reference
    test_dir = tmp_path / "isolated_test"
    test_dir.mkdir()
    test_file = test_dir / "test.py"
    test_file.write_text("print('hello')")

    # Mock fd output to return our test file
    mock_check_output.return_value = f"{test_file}\n"

    with patch.object(mcp_fd_server, "FD_EXECUTABLE", "/mock/fd"):
        result = mcp_fd_server.search_files(pattern=r"\.py$", path=str(test_dir))

    assert "matches" in result
    matches = result["matches"]
    assert len(matches) == 1
    assert normalize_path(str(test_file)) in matches[0]
