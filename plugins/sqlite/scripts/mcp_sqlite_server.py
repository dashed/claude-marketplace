#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=0.1.0"]
#
# [project.optional-dependencies]
# dev = ["pytest>=7.0", "pytest-asyncio>=0.21.0"]
# ///
"""
`mcp_sqlite_server.py` – **Model Context Protocol** server for SQLite database operations.

This server provides a simple, agent-friendly interface to SQLite databases with
configurable read/write permissions.

Tools exposed to LLMs
--------------------
* **`query`** – Execute a SELECT query and return results
* **`execute`** – Execute INSERT, UPDATE, DELETE queries (if writes enabled)
* **`list_tables`** – List all tables in the database
* **`describe_table`** – Get schema information for a specific table
* **`create_table`** – Create a new table (if writes enabled)

Database Path (db_path) Examples
-------------------------------
All tools accept an optional `db_path` parameter:

* **Default**: Uses the db_path configured when starting the server
* **Relative path**: `'data.db'`, `'./databases/app.db'`
* **Absolute path**: `'/var/lib/myapp/data.db'`, `'C:\\Users\\Me\\data.db'`
* **In-memory**: `':memory:'` - Creates a temporary in-memory database
* **Home directory**: `'~/myapp/data.db'` - Expands to user's home directory

Quick start
-----------
```bash
chmod +x mcp_sqlite_server.py

# 1. CLI usage
./mcp_sqlite_server.py query "SELECT * FROM users" database.db
./mcp_sqlite_server.py list-tables database.db
./mcp_sqlite_server.py describe-table users database.db

# 2. Run as MCP server with default database
./mcp_sqlite_server.py --db-path /path/to/default.db

# 3. Run with write permissions
./mcp_sqlite_server.py --allow-writes --db-path /path/to/default.db
```

Configuration
------------
Write operations are disabled by default for safety. Enable with:
- CLI flag: --allow-writes
- Environment variable: MCP_SQLITE_ALLOW_WRITES=true

Default database path can be set with:
- CLI flag: --db-path /path/to/database.db
- Or specify db_path in each tool call
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Check environment variable for write permission
ALLOW_WRITES = os.environ.get("MCP_SQLITE_ALLOW_WRITES", "false").lower() in (
    "true",
    "1",
    "yes",
)


class SQLiteContext:
    """Context for SQLite operations."""

    def __init__(self, db_path: str | None = None, allow_writes: bool = False):
        self.db_path = db_path
        self.allow_writes = allow_writes
        self._memory_conn: sqlite3.Connection | None = None

    def get_connection(self, db_path: str | None = None) -> sqlite3.Connection:
        """Get a connection to the SQLite database."""
        path = db_path or self.db_path
        if not path:
            raise ValueError("No database path provided")

        # Handle in-memory database specially to maintain state
        if path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:")
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn

        # Expand home directory if present
        if path.startswith("~"):
            path = str(Path(path).expanduser())

        # Ensure the database file exists or can be created
        db_file = Path(path)
        if not db_file.exists() and not self.allow_writes:
            raise ValueError(f"Database {path} does not exist (writes disabled)")

        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn


# ---------------------------------------------------------------------------
# MCP Server Setup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[SQLiteContext]:
    """Initialize SQLite context on startup."""
    # Get configuration from command line or environment
    parser = argparse.ArgumentParser(description="SQLite MCP Server")
    parser.add_argument(
        "--allow-writes",
        action="store_true",
        help="Allow write operations (INSERT, UPDATE, DELETE, CREATE TABLE)",
    )
    parser.add_argument(
        "--db-path", type=str, help="Default database path", default=None
    )

    # Parse known args to allow MCP to handle its own args
    args, _ = parser.parse_known_args()

    # Override with environment variable if set
    allow_writes = args.allow_writes or ALLOW_WRITES

    logger.info(
        f"SQLite MCP Server started (writes: {'enabled' if allow_writes else 'disabled'})"
    )

    context = SQLiteContext(db_path=args.db_path, allow_writes=allow_writes)
    yield context


mcp = FastMCP("SQLite Database", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Tool: query
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Execute a SELECT query on the SQLite database.\n\n"
        "Args:\n"
        "  query (str): The SELECT query to execute\n"
        "  db_path (str, optional): Path to the database file. Uses default if not provided.\n\n"
        "Returns:\n"
        "  List of dictionaries representing rows, or error message\n\n"
        "Examples:\n"
        "  query('SELECT * FROM users')  # Uses default db_path\n"
        "  query('SELECT * FROM users', 'myapp.db')  # Specific database\n"
        "  query('SELECT * FROM users', '/path/to/data.db')  # Absolute path\n"
        "  query('SELECT * FROM users', ':memory:')  # In-memory database\n"
        "  query('SELECT name, email FROM users WHERE active = 1', 'users.db')\n"
        "  query('SELECT COUNT(*) as count FROM orders', 'sales.db')"
    )
)
async def query(query: str, db_path: str | None = None) -> dict[str, Any]:
    """Execute a SELECT query and return results."""
    context: SQLiteContext = mcp.context  # type: ignore[attr-defined]

    if not query.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed in query tool"}

    try:
        conn = context.get_connection(db_path)
        cursor = conn.execute(query)
        rows = cursor.fetchall()

        # Convert Row objects to dictionaries
        results = []
        for row in rows:
            results.append(dict(row))

        conn.close()
        return {"results": results, "row_count": len(results)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool: execute
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Execute INSERT, UPDATE, or DELETE queries on the SQLite database.\n"
        "**Note: Requires write permissions to be enabled.**\n\n"
        "Args:\n"
        "  query (str): The SQL query to execute\n"
        "  db_path (str, optional): Path to the database file. Uses default if not provided.\n\n"
        "Returns:\n"
        "  Success status with affected row count, or error message\n\n"
        "Examples:\n"
        '  execute(\'INSERT INTO users (name, email) VALUES ("John", "john@example.com")\')  # Uses default db_path\n'
        "  execute('INSERT INTO logs (message) VALUES (\"Started\")', 'app.db')  # Specific database\n"
        "  execute('UPDATE users SET active = 0 WHERE id = 5', '/var/data/users.db')  # Absolute path\n"
        "  execute('UPDATE settings SET value = \"dark\" WHERE key = \"theme\"', ':memory:')  # In-memory database\n"
        "  execute('UPDATE users SET active = 0 WHERE last_login < date(\"now\", \"-1 year\")', 'users.db')\n"
        "  execute('DELETE FROM sessions WHERE expired = 1', 'sessions.db')"
    )
)
async def execute(query: str, db_path: str | None = None) -> dict[str, Any]:
    """Execute INSERT, UPDATE, or DELETE queries."""
    context: SQLiteContext = mcp.context  # type: ignore[attr-defined]

    if not context.allow_writes:
        return {
            "error": "Write operations are disabled. Run server with --allow-writes flag or set MCP_SQLITE_ALLOW_WRITES=true"
        }

    # Basic safety check - only allow specific write operations
    query_upper = query.strip().upper()
    if not any(query_upper.startswith(op) for op in ["INSERT", "UPDATE", "DELETE"]):
        return {
            "error": "Only INSERT, UPDATE, and DELETE queries are allowed in execute tool"
        }

    try:
        conn = context.get_connection(db_path)
        cursor = conn.execute(query)
        conn.commit()

        affected_rows = cursor.rowcount
        conn.close()

        return {"success": True, "affected_rows": affected_rows}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool: list_tables
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "List all tables in the SQLite database.\n\n"
        "Args:\n"
        "  db_path (str, optional): Path to the database file. Uses default if not provided.\n\n"
        "Returns:\n"
        "  List of table names in the database\n\n"
        "Examples:\n"
        "  list_tables()  # Uses default db_path\n"
        "  list_tables('myapp.db')  # Specific database file\n"
        "  list_tables('/path/to/database.db')  # Absolute path\n"
        "  list_tables(':memory:')  # List tables in in-memory database\n"
        "  list_tables('./data/analytics.db')  # Relative path"
    )
)
async def list_tables(db_path: str | None = None) -> dict[str, Any]:
    """List all tables in the database."""
    context: SQLiteContext = mcp.context  # type: ignore[attr-defined]

    try:
        conn = context.get_connection(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        conn.close()

        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool: describe_table
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Get schema information for a specific table.\n\n"
        "Args:\n"
        "  table_name (str): Name of the table to describe\n"
        "  db_path (str, optional): Path to the database file. Uses default if not provided.\n\n"
        "Returns:\n"
        "  Table schema including columns, types, and constraints\n\n"
        "Examples:\n"
        "  describe_table('users')  # Uses default db_path\n"
        "  describe_table('products', 'store.db')  # Specific database\n"
        "  describe_table('logs', '/var/log/app.db')  # Absolute path\n"
        "  describe_table('cache', ':memory:')  # In-memory database\n"
        "  describe_table('settings', './config/app.db')  # Relative path"
    )
)
async def describe_table(table_name: str, db_path: str | None = None) -> dict[str, Any]:
    """Get detailed information about a table's schema."""
    context: SQLiteContext = mcp.context  # type: ignore[attr-defined]

    try:
        conn = context.get_connection(db_path)

        # Get column information
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append(
                {
                    "name": row["name"],
                    "type": row["type"],
                    "nullable": not row["notnull"],
                    "default": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
            )

        # Get table creation SQL
        cursor = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        result = cursor.fetchone()
        create_sql = result["sql"] if result else None

        # Get indexes
        cursor = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=?",
            (table_name,),
        )
        indexes = [
            {"name": row["name"], "sql": row["sql"]} for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "table_name": table_name,
            "columns": columns,
            "create_sql": create_sql,
            "indexes": indexes,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool: create_table
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Create a new table in the database.\n"
        "**Note: Requires write permissions to be enabled.**\n\n"
        "Args:\n"
        "  table_name (str): Name of the table to create\n"
        "  columns (list): List of column definitions, each with 'name', 'type', and optional 'constraints'\n"
        "  db_path (str, optional): Path to the database file. Uses default if not provided.\n\n"
        "Column definition format:\n"
        "  {'name': 'id', 'type': 'INTEGER', 'constraints': 'PRIMARY KEY AUTOINCREMENT'}\n"
        "  {'name': 'email', 'type': 'TEXT', 'constraints': 'UNIQUE NOT NULL'}\n"
        "  {'name': 'created_at', 'type': 'TIMESTAMP', 'constraints': 'DEFAULT CURRENT_TIMESTAMP'}\n\n"
        "Returns:\n"
        "  Success status or error message\n\n"
        "Examples:\n"
        "  # Uses default db_path\n"
        "  create_table('users', [{'name': 'id', 'type': 'INTEGER', 'constraints': 'PRIMARY KEY'}])\n"
        "  \n"
        "  # Specific database file\n"
        "  create_table('products', [...], 'store.db')\n"
        "  \n"
        "  # Absolute path\n"
        "  create_table('logs', [...], '/var/data/app.db')\n"
        "  \n"
        "  # In-memory database for testing\n"
        "  create_table('temp_data', [...], ':memory:')\n"
        "  \n"
        "  # Relative path\n"
        "  create_table('settings', [...], './config/app.db')"
    )
)
async def create_table(
    table_name: str,
    columns: list[dict[str, str]],
    db_path: str | None = None,
) -> dict[str, Any]:
    """Create a new table with specified columns."""
    context: SQLiteContext = mcp.context  # type: ignore[attr-defined]

    if not context.allow_writes:
        return {
            "error": "Write operations are disabled. Run server with --allow-writes flag or set MCP_SQLITE_ALLOW_WRITES=true"
        }

    try:
        # Build CREATE TABLE statement
        column_defs = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if "constraints" in col:
                col_def += f" {col['constraints']}"
            column_defs.append(col_def)

        create_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"

        conn = context.get_connection(db_path)
        conn.execute(create_sql)
        conn.commit()
        conn.close()

        return {"success": True, "table_name": table_name, "sql": create_sql}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------


def _query_sync(
    context: SQLiteContext, query_str: str, db_path: str | None = None
) -> dict[str, Any]:
    """Synchronous version of query for CLI."""
    if not query_str.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed in query tool"}

    try:
        conn = context.get_connection(db_path)
        cursor = conn.execute(query_str)
        rows = cursor.fetchall()

        # Convert Row objects to dictionaries
        results = []
        for row in rows:
            results.append(dict(row))

        conn.close()
        return {"results": results, "row_count": len(results)}
    except Exception as e:
        return {"error": str(e)}


def _list_tables_sync(
    context: SQLiteContext, db_path: str | None = None
) -> dict[str, Any]:
    """Synchronous version of list_tables for CLI."""
    try:
        conn = context.get_connection(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        conn.close()

        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e)}


def _describe_table_sync(
    context: SQLiteContext, table_name: str, db_path: str | None = None
) -> dict[str, Any]:
    """Synchronous version of describe_table for CLI."""
    try:
        conn = context.get_connection(db_path)

        # Get column information
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append(
                {
                    "name": row["name"],
                    "type": row["type"],
                    "nullable": not row["notnull"],
                    "default": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
            )

        # Get table creation SQL
        cursor = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        result = cursor.fetchone()
        create_sql = result["sql"] if result else None

        # Get indexes
        cursor = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=?",
            (table_name,),
        )
        indexes = [
            {"name": row["name"], "sql": row["sql"]} for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "table_name": table_name,
            "columns": columns,
            "create_sql": create_sql,
            "indexes": indexes,
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """CLI interface for testing SQLite operations."""
    parser = argparse.ArgumentParser(description="SQLite MCP Server CLI")
    parser.add_argument(
        "--allow-writes",
        action="store_true",
        help="Allow write operations",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Query command
    query_parser = subparsers.add_parser("query", help="Execute a SELECT query")
    query_parser.add_argument("query", help="SQL query to execute")
    query_parser.add_argument("db_path", help="Path to SQLite database")

    # List tables command
    list_parser = subparsers.add_parser("list-tables", help="List all tables")
    list_parser.add_argument("db_path", help="Path to SQLite database")

    # Describe table command
    describe_parser = subparsers.add_parser("describe-table", help="Describe a table")
    describe_parser.add_argument("table_name", help="Name of the table")
    describe_parser.add_argument("db_path", help="Path to SQLite database")

    args = parser.parse_args()

    if not args.command:
        # Run as MCP server
        mcp.run()
        return

    # Create context for CLI operations
    context = SQLiteContext(allow_writes=args.allow_writes)

    # Execute command
    if args.command == "query":
        result = _query_sync(context, args.query, args.db_path)
    elif args.command == "list-tables":
        result = _list_tables_sync(context, args.db_path)
    elif args.command == "describe-table":
        result = _describe_table_sync(context, args.table_name, args.db_path)
    else:
        print(f"Unknown command: {args.command}")
        return

    # Print result
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
