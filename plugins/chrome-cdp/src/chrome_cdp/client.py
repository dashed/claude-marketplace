"""CDP WebSocket client — async interface to Chrome DevTools Protocol."""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from .helpers import TIMEOUT


@dataclass
class EventWaiter:
    """A pending event wait with a future and cancel method."""

    future: asyncio.Future[dict[str, Any]]
    _cancel: Callable[[], None] | None = field(default=None, repr=False)

    def cancel(self) -> None:
        if self._cancel:
            self._cancel()


class CDPClient:
    """Async Chrome DevTools Protocol WebSocket client."""

    def __init__(self) -> None:
        self._ws: ClientConnection | None = None
        self._id: int = 0
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._event_handlers: dict[str, set[Callable[..., Any]]] = {}
        self._close_handlers: list[Callable[[], None]] = []
        self._reader_task: asyncio.Task[None] | None = None

    async def connect(self, ws_url: str) -> None:
        """Connect to a Chrome DevTools Protocol WebSocket endpoint."""
        self._ws = await websockets.connect(ws_url, max_size=50 * 1024 * 1024)
        self._reader_task = asyncio.create_task(self._read_loop())

    async def _read_loop(self) -> None:
        """Background task that reads messages and dispatches them."""
        assert self._ws is not None
        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                msg_id = msg.get("id")
                if msg_id is not None and msg_id in self._pending:
                    fut = self._pending.pop(msg_id)
                    if not fut.done():
                        if msg.get("error"):
                            fut.set_exception(RuntimeError(msg["error"]["message"]))
                        else:
                            fut.set_result(msg.get("result"))
                elif msg.get("method") and msg["method"] in self._event_handlers:
                    for handler in list(self._event_handlers[msg["method"]]):
                        handler(msg.get("params", {}), msg)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception:
            pass
        finally:
            self._fire_close_handlers()
            # Reject all pending requests
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(RuntimeError("WebSocket connection closed"))
            self._pending.clear()

    def _fire_close_handlers(self) -> None:
        for handler in self._close_handlers:
            with contextlib.suppress(Exception):
                handler()

    async def send(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        session_id: str | None = None,
        timeout: float = TIMEOUT,
    ) -> Any:
        """Send a CDP command and wait for the response."""
        assert self._ws is not None
        self._id += 1
        msg_id = self._id
        msg: dict[str, Any] = {"id": msg_id, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id

        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self._pending[msg_id] = fut

        await self._ws.send(json.dumps(msg))

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(msg_id, None)
            raise RuntimeError(f"Timeout: {method}") from None

    def on_event(self, method: str, handler: Callable[..., Any]) -> Callable[[], None]:
        """Register an event handler. Returns an unsubscribe function."""
        if method not in self._event_handlers:
            self._event_handlers[method] = set()
        self._event_handlers[method].add(handler)

        def off() -> None:
            handlers = self._event_handlers.get(method)
            if handlers:
                handlers.discard(handler)
                if not handlers:
                    del self._event_handlers[method]

        return off

    def wait_for_event(self, method: str, timeout: float = TIMEOUT) -> EventWaiter:
        """Wait for a single occurrence of an event. Returns an EventWaiter."""
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        settled = False

        def handler(params: dict[str, Any], _msg: Any) -> None:
            nonlocal settled
            if settled:
                return
            settled = True
            if off:
                off()
            if not fut.done():
                fut.set_result(params)

        off = self.on_event(method, handler)

        timeout_handle = loop.call_later(
            timeout,
            lambda: _timeout_handler(fut, off, method),
        )

        def cancel() -> None:
            nonlocal settled
            if settled:
                return
            settled = True
            timeout_handle.cancel()
            if off:
                off()
            if not fut.done():
                fut.cancel()

        def _timeout_handler(
            f: asyncio.Future[dict[str, Any]],
            unsub: Callable[[], None],
            m: str,
        ) -> None:
            nonlocal settled
            if settled:
                return
            settled = True
            unsub()
            if not f.done():
                f.set_exception(RuntimeError(f"Timeout waiting for event: {m}"))

        return EventWaiter(future=fut, _cancel=cancel)

    def on_close(self, handler: Callable[[], None]) -> None:
        """Register a handler to be called when the connection closes."""
        self._close_handlers.append(handler)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
