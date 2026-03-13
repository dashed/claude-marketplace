"""Shared fixtures for chrome-cdp tests."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chrome_cdp.client import CDPClient


@pytest.fixture
def sample_pages() -> list[dict[str, Any]]:
    """Sample page data as returned by Target.getTargets."""
    return [
        {
            "targetId": "AABB1122CCDD3344",
            "type": "page",
            "title": "Example Page",
            "url": "https://example.com",
        },
        {
            "targetId": "EEFF5566GGHH7788",
            "type": "page",
            "title": "Another Page",
            "url": "https://another.com",
        },
        {
            "targetId": "AABB1122XXXX9999",
            "type": "page",
            "title": "Third Page",
            "url": "https://third.com",
        },
    ]


@pytest.fixture
def sample_ax_nodes() -> list[dict[str, Any]]:
    """Sample accessibility tree nodes."""
    return [
        {
            "nodeId": "1",
            "role": {"value": "RootWebArea"},
            "name": {"value": "Test Page"},
            "childIds": ["2", "3"],
        },
        {
            "nodeId": "2",
            "parentId": "1",
            "role": {"value": "heading"},
            "name": {"value": "Main Title"},
            "childIds": [],
        },
        {
            "nodeId": "3",
            "parentId": "1",
            "role": {"value": "link"},
            "name": {"value": "Click Me"},
            "value": {"value": "https://example.com"},
            "childIds": [],
        },
        {
            "nodeId": "4",
            "parentId": "1",
            "role": {"value": "generic"},
            "name": {"value": ""},
            "childIds": [],
        },
        {
            "nodeId": "5",
            "parentId": "1",
            "role": {"value": "none"},
            "name": {"value": "hidden"},
            "childIds": [],
        },
    ]


@pytest.fixture
def mock_ws() -> MagicMock:
    """Mock websocket connection."""
    ws = AsyncMock()
    ws.close = AsyncMock()
    ws.send = AsyncMock()
    return ws


@pytest.fixture
def cdp_client() -> CDPClient:
    """A fresh CDPClient instance (not connected)."""
    return CDPClient()


@pytest.fixture
def connected_cdp_client(cdp_client: CDPClient, mock_ws: MagicMock) -> CDPClient:
    """A CDPClient with a mocked websocket connection and no reader task."""
    cdp_client._ws = mock_ws
    # Don't start a reader task — tests that need one will manage it themselves
    return cdp_client


@pytest.fixture
def temp_sock_dir(tmp_path):
    """Provide a temporary directory for socket files."""
    return tmp_path
