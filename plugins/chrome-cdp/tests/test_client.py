"""Tests for chrome_cdp.client — CDP WebSocket client."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chrome_cdp.client import CDPClient, EventWaiter


# ── CDPClient init ─────────────────────────────────────────────────────────


class TestCDPClientInit:
    def test_initial_state(self):
        client = CDPClient()
        assert client._ws is None
        assert client._id == 0
        assert client._pending == {}
        assert client._event_handlers == {}
        assert client._close_handlers == []
        assert client._reader_task is None


# ── CDPClient.connect ──────────────────────────────────────────────────────


class TestCDPClientConnect:
    async def test_connect_sets_ws_and_starts_reader(self):
        client = CDPClient()
        mock_ws = AsyncMock()
        # Make the websocket iterable but immediately stop
        mock_ws.__aiter__ = MagicMock(return_value=AsyncMock(__anext__=AsyncMock(side_effect=StopAsyncIteration)))

        with patch("chrome_cdp.client.websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_ws
            await client.connect("ws://127.0.0.1:9222/devtools/browser/test")

            assert client._ws is mock_ws
            assert client._reader_task is not None

            # Clean up
            await client.close()


# ── CDPClient.send ─────────────────────────────────────────────────────────


class TestCDPClientSend:
    async def test_send_increments_id(self, connected_cdp_client):
        client = connected_cdp_client

        # Simulate response arriving for each send
        async def fake_send(data):
            msg = json.loads(data)
            loop = asyncio.get_running_loop()
            # Schedule response delivery
            loop.call_soon(
                lambda mid=msg["id"]: client._pending[mid].set_result({"ok": True})
                if mid in client._pending
                else None
            )

        client._ws.send = fake_send

        await client.send("Test.method1", timeout=1.0)
        assert client._id == 1

        await client.send("Test.method2", timeout=1.0)
        assert client._id == 2

    async def test_send_includes_session_id(self, connected_cdp_client):
        client = connected_cdp_client
        sent_data = None

        async def capture_send(data):
            nonlocal sent_data
            sent_data = json.loads(data)
            loop = asyncio.get_running_loop()
            loop.call_soon(
                lambda: client._pending[sent_data["id"]].set_result({})
                if sent_data["id"] in client._pending
                else None
            )

        client._ws.send = capture_send
        await client.send("Test.method", {"key": "val"}, session_id="sess-1", timeout=1.0)

        assert sent_data is not None
        assert sent_data["sessionId"] == "sess-1"
        assert sent_data["params"] == {"key": "val"}

    async def test_send_timeout_raises(self, connected_cdp_client):
        client = connected_cdp_client
        # Don't resolve the future — it will time out
        with pytest.raises(RuntimeError, match="Timeout"):
            await client.send("Slow.method", timeout=0.05)

    async def test_send_error_response(self, connected_cdp_client):
        """Test that CDP error responses are propagated via the read loop."""
        client = connected_cdp_client

        async def fake_send(data):
            msg = json.loads(data)
            loop = asyncio.get_running_loop()
            loop.call_soon(
                lambda mid=msg["id"]: client._pending[mid].set_exception(
                    RuntimeError("Something went wrong")
                )
                if mid in client._pending and not client._pending[mid].done()
                else None
            )

        client._ws.send = fake_send
        with pytest.raises(RuntimeError, match="Something went wrong"):
            await client.send("Error.method", timeout=1.0)


# ── CDPClient.on_event / wait_for_event ────────────────────────────────────


class TestCDPClientEvents:
    def test_on_event_registers_handler(self, cdp_client):
        handler = MagicMock()
        off = cdp_client.on_event("Page.loadEventFired", handler)

        assert "Page.loadEventFired" in cdp_client._event_handlers
        assert handler in cdp_client._event_handlers["Page.loadEventFired"]

        # Unsubscribe
        off()
        assert "Page.loadEventFired" not in cdp_client._event_handlers

    def test_on_event_multiple_handlers(self, cdp_client):
        h1 = MagicMock()
        h2 = MagicMock()
        off1 = cdp_client.on_event("Page.loadEventFired", h1)
        cdp_client.on_event("Page.loadEventFired", h2)

        assert len(cdp_client._event_handlers["Page.loadEventFired"]) == 2

        # Removing one keeps the other
        off1()
        assert h2 in cdp_client._event_handlers["Page.loadEventFired"]
        assert h1 not in cdp_client._event_handlers["Page.loadEventFired"]

    async def test_wait_for_event_resolves(self, cdp_client):
        cdp_client._ws = MagicMock()  # Need ws to look connected
        waiter = cdp_client.wait_for_event("Page.loadEventFired", timeout=5.0)

        assert isinstance(waiter, EventWaiter)
        assert not waiter.future.done()

        # Simulate the event firing
        handlers = cdp_client._event_handlers.get("Page.loadEventFired", set())
        for h in list(handlers):
            h({"timestamp": 12345}, {"method": "Page.loadEventFired"})

        result = await waiter.future
        assert result == {"timestamp": 12345}

    async def test_wait_for_event_timeout(self, cdp_client):
        cdp_client._ws = MagicMock()
        waiter = cdp_client.wait_for_event("Never.fires", timeout=0.05)

        with pytest.raises(RuntimeError, match="Timeout waiting for event"):
            await waiter.future

    async def test_wait_for_event_cancel(self, cdp_client):
        cdp_client._ws = MagicMock()
        waiter = cdp_client.wait_for_event("Page.loadEventFired", timeout=5.0)

        waiter.cancel()
        assert waiter.future.cancelled()


# ── CDPClient.on_close ─────────────────────────────────────────────────────


class TestCDPClientOnClose:
    def test_on_close_registers_handler(self, cdp_client):
        handler = MagicMock()
        cdp_client.on_close(handler)
        assert handler in cdp_client._close_handlers

    def test_fire_close_handlers(self, cdp_client):
        h1 = MagicMock()
        h2 = MagicMock()
        cdp_client.on_close(h1)
        cdp_client.on_close(h2)

        cdp_client._fire_close_handlers()
        h1.assert_called_once()
        h2.assert_called_once()

    def test_fire_close_handlers_suppresses_exceptions(self, cdp_client):
        h1 = MagicMock(side_effect=RuntimeError("boom"))
        h2 = MagicMock()
        cdp_client.on_close(h1)
        cdp_client.on_close(h2)

        # Should not raise
        cdp_client._fire_close_handlers()
        h2.assert_called_once()


# ── CDPClient.close ────────────────────────────────────────────────────────


class TestCDPClientClose:
    async def test_close_with_no_connection(self, cdp_client):
        # Should not raise
        await cdp_client.close()

    async def test_close_closes_ws(self, connected_cdp_client):
        client = connected_cdp_client
        await client.close()
        client._ws.close.assert_awaited_once()


# ── CDPClient._read_loop ──────────────────────────────────────────────────


class TestCDPClientReadLoop:
    async def test_read_loop_dispatches_response(self):
        """Test that the read loop resolves pending futures from responses."""
        client = CDPClient()
        response_msg = json.dumps({"id": 1, "result": {"data": "test"}})

        mock_ws = AsyncMock()
        mock_ws.__aiter__ = MagicMock(return_value=iter([response_msg]))

        client._ws = mock_ws

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        client._pending[1] = fut

        await client._read_loop()

        assert fut.done()
        assert fut.result() == {"data": "test"}

    async def test_read_loop_dispatches_error_response(self):
        """Test that the read loop rejects futures from error responses."""
        client = CDPClient()
        error_msg = json.dumps({"id": 1, "error": {"message": "Not found"}})

        mock_ws = AsyncMock()
        mock_ws.__aiter__ = MagicMock(return_value=iter([error_msg]))

        client._ws = mock_ws

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        client._pending[1] = fut

        await client._read_loop()

        assert fut.done()
        with pytest.raises(RuntimeError, match="Not found"):
            fut.result()

    async def test_read_loop_dispatches_events(self):
        """Test that the read loop calls event handlers."""
        client = CDPClient()
        event_msg = json.dumps(
            {"method": "Page.loadEventFired", "params": {"timestamp": 100}}
        )

        mock_ws = AsyncMock()
        mock_ws.__aiter__ = MagicMock(return_value=iter([event_msg]))

        client._ws = mock_ws

        handler = MagicMock()
        client.on_event("Page.loadEventFired", handler)

        await client._read_loop()

        handler.assert_called_once_with(
            {"timestamp": 100}, {"method": "Page.loadEventFired", "params": {"timestamp": 100}}
        )

    async def test_read_loop_fires_close_handlers_on_finish(self):
        """Test that close handlers fire when the read loop ends."""
        client = CDPClient()

        mock_ws = AsyncMock()
        mock_ws.__aiter__ = MagicMock(return_value=iter([]))

        client._ws = mock_ws

        close_handler = MagicMock()
        client.on_close(close_handler)

        await client._read_loop()

        close_handler.assert_called_once()

    async def test_read_loop_rejects_pending_on_close(self):
        """Test that remaining pending futures are rejected when loop ends."""
        client = CDPClient()

        mock_ws = AsyncMock()
        mock_ws.__aiter__ = MagicMock(return_value=iter([]))

        client._ws = mock_ws

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        client._pending[99] = fut

        await client._read_loop()

        assert fut.done()
        with pytest.raises(RuntimeError, match="WebSocket connection closed"):
            fut.result()
        assert client._pending == {}


# ── EventWaiter ────────────────────────────────────────────────────────────


class TestEventWaiter:
    def test_cancel_with_no_cancel_func(self):
        loop = asyncio.new_event_loop()
        fut = loop.create_future()
        waiter = EventWaiter(future=fut)
        # Should not raise
        waiter.cancel()
        loop.close()

    def test_cancel_calls_cancel_func(self):
        loop = asyncio.new_event_loop()
        fut = loop.create_future()
        cancel_fn = MagicMock()
        waiter = EventWaiter(future=fut, _cancel=cancel_fn)
        waiter.cancel()
        cancel_fn.assert_called_once()
        loop.close()
