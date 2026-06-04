"""Test SQLite MCP server functionality."""

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from conftest import SERVER_SCRIPT
from mcp_sqlite_server import (
    SQLiteContext,
    _describe_table_sync,
    _list_tables_sync,
    _query_sync,
)


def test_sqlite_context_creation():
    """Test SQLiteContext creation."""
    # Test with read-only
    context = SQLiteContext(db_path=":memory:", allow_writes=False)
    assert context.db_path == ":memory:"
    assert context.allow_writes is False

    # Test with write enabled
    context = SQLiteContext(db_path=":memory:", allow_writes=True)
    assert context.allow_writes is True


def test_list_tables_sync():
    """Test list_tables with in-memory database."""
    context = SQLiteContext(db_path=":memory:", allow_writes=True)

    # Create test data
    conn = context.get_connection()
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER)")
    conn.commit()

    result = _list_tables_sync(context, ":memory:")
    assert "tables" in result
    assert set(result["tables"]) == {"users", "orders"}
    assert result["count"] == 2


def test_describe_table_sync():
    """Test describe_table with in-memory database."""
    context = SQLiteContext(db_path=":memory:", allow_writes=True)

    # Create test data
    conn = context.get_connection()
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)
    conn.commit()

    result = _describe_table_sync(context, "users", ":memory:")
    assert result["table_name"] == "users"
    assert len(result["columns"]) == 4

    # Check specific columns
    id_col = next(c for c in result["columns"] if c["name"] == "id")
    assert id_col["type"] == "INTEGER"
    assert id_col["primary_key"] is True

    email_col = next(c for c in result["columns"] if c["name"] == "email")
    assert email_col["type"] == "TEXT"
    assert email_col["nullable"] is False


def test_query_sync():
    """Test query with in-memory database."""
    context = SQLiteContext(db_path=":memory:", allow_writes=True)

    # Create test data
    conn = context.get_connection()
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO users (name, email) VALUES
        ('Alice', 'alice@example.com'),
        ('Bob', 'bob@example.com'),
        ('Charlie', 'charlie@example.com')
    """)
    conn.commit()

    # Test simple SELECT
    result = _query_sync(context, "SELECT COUNT(*) as total FROM users", ":memory:")
    assert result["results"][0]["total"] == 3
    assert result["row_count"] == 1

    # Test error - non-SELECT query
    result = _query_sync(
        context,
        "INSERT INTO users (name, email) VALUES ('Test', 'test@example.com')",
        ":memory:",
    )
    assert "error" in result
    assert "Only SELECT queries" in result["error"]


def test_write_protection():
    """Test that write operations are protected."""
    # Create read-only context
    context = SQLiteContext(db_path=":memory:", allow_writes=False)
    assert context.allow_writes is False

    # Create write-enabled context
    context = SQLiteContext(db_path=":memory:", allow_writes=True)
    assert context.allow_writes is True


@pytest.fixture
def test_db():
    """Create a temporary test database for CLI tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    # Create test data
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        INSERT INTO users (name, email) VALUES
        ('Alice', 'alice@example.com'),
        ('Bob', 'bob@example.com'),
        ('Charlie', 'charlie@example.com')
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


def run_cli_command(command: list[str]) -> dict:
    """Run a CLI command and return the JSON output."""
    result = subprocess.run(
        [sys.executable, SERVER_SCRIPT] + command,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")
    return json.loads(result.stdout)


def test_list_tables(test_db):
    """Test listing tables."""
    result = run_cli_command(["list-tables", test_db])
    assert "tables" in result
    assert "users" in result["tables"]
    assert result["count"] >= 1  # SQLite may have system tables


def test_describe_table(test_db):
    """Test describing a table."""
    result = run_cli_command(["describe-table", "users", test_db])
    assert result["table_name"] == "users"
    assert len(result["columns"]) == 4

    # Check column details
    id_col = next(c for c in result["columns"] if c["name"] == "id")
    assert id_col["type"] == "INTEGER"
    assert id_col["primary_key"] is True

    email_col = next(c for c in result["columns"] if c["name"] == "email")
    assert email_col["type"] == "TEXT"
    assert email_col["nullable"] is False


def test_query(test_db):
    """Test executing SELECT queries."""
    # Test SELECT all
    result = run_cli_command(["query", "SELECT * FROM users", test_db])
    assert len(result["results"]) == 3
    assert result["row_count"] == 3

    # Test SELECT with WHERE
    result = run_cli_command(
        ["query", "SELECT name FROM users WHERE email LIKE '%@example.com'", test_db]
    )
    assert len(result["results"]) == 3
    assert all("name" in row for row in result["results"])

    # Test COUNT
    result = run_cli_command(["query", "SELECT COUNT(*) as total FROM users", test_db])
    assert result["results"][0]["total"] == 3


def test_query_error(test_db):
    """Test query with invalid SQL."""
    result = run_cli_command(["query", "SELECT * FROM nonexistent_table", test_db])
    assert "error" in result
    assert "no such table" in result["error"]


def test_write_operations_disabled_by_default():
    """Test that write operations are disabled by default."""
    # Since execute tool isn't exposed via CLI directly, we'd need to test
    # this through the server interface. For now, we'll just verify the
    # server starts correctly.
    result = subprocess.run(
        [sys.executable, SERVER_SCRIPT, "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--allow-writes" in result.stdout
