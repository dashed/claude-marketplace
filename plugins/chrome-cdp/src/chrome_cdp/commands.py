"""Command implementations — return strings, take (cdp, session_id)."""

from __future__ import annotations

import asyncio
import base64
import json
import math
from pathlib import Path
from typing import Any

from .client import CDPClient
from .helpers import NAVIGATION_TIMEOUT, get_display_prefix_length


async def get_pages(cdp: CDPClient) -> list[dict[str, Any]]:
    """List open pages, filtering out chrome:// URLs."""
    result = await cdp.send("Target.getTargets")
    return [
        t
        for t in result["targetInfos"]
        if t.get("type") == "page" and not t.get("url", "").startswith("chrome://")
    ]


def format_page_list(pages: list[dict[str, Any]]) -> str:
    """Format a list of pages into a human-readable table."""
    prefix_len = get_display_prefix_length([p["targetId"] for p in pages])
    lines: list[str] = []
    for p in pages:
        tid = p["targetId"][:prefix_len].ljust(prefix_len)
        title = p.get("title", "")[:54].ljust(54)
        url = p.get("url", "")
        lines.append(f"{tid}  {title}  {url}")
    return "\n".join(lines)


def should_show_ax_node(node: dict[str, Any], compact: bool = False) -> bool:
    """Determine whether an accessibility node should be displayed."""
    role = (node.get("role") or {}).get("value", "")
    name = (node.get("name") or {}).get("value", "")
    value = (node.get("value") or {}).get("value")
    if compact and role == "InlineTextBox":
        return False
    if role in ("none", "generic"):
        return False
    return not (name == "" and (value == "" or value is None))


def format_ax_node(node: dict[str, Any], depth: int) -> str:
    """Format an accessibility node as an indented line."""
    role = (node.get("role") or {}).get("value", "")
    name = (node.get("name") or {}).get("value", "")
    value = (node.get("value") or {}).get("value")
    indent = "  " * min(depth, 10)
    line = f"{indent}[{role}]"
    if name != "":
        line += f" {name}"
    if not (value == "" or value is None):
        line += f" = {json.dumps(value)}"
    return line


def ordered_ax_children(
    node: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    children_by_parent: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Get children of an accessibility node in display order."""
    children: list[dict[str, Any]] = []
    seen: set[str] = set()
    for child_id in node.get("childIds", []):
        child = nodes_by_id.get(child_id)
        if child and child["nodeId"] not in seen:
            seen.add(child["nodeId"])
            children.append(child)
    for child in children_by_parent.get(node["nodeId"], []):
        if child["nodeId"] not in seen:
            seen.add(child["nodeId"])
            children.append(child)
    return children


async def snapshot_str(cdp: CDPClient, sid: str, compact: bool = False) -> str:
    """Get accessibility tree snapshot as a formatted string."""
    result = await cdp.send("Accessibility.getFullAXTree", {}, sid)
    nodes: list[dict[str, Any]] = result["nodes"]

    nodes_by_id: dict[str, dict[str, Any]] = {n["nodeId"]: n for n in nodes}
    children_by_parent: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        parent_id = node.get("parentId")
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(node)

    lines: list[str] = []
    visited: set[str] = set()

    def visit(node: dict[str, Any], depth: int) -> None:
        nid = node["nodeId"]
        if nid in visited:
            return
        visited.add(nid)
        if should_show_ax_node(node, compact):
            lines.append(format_ax_node(node, depth))
        for child in ordered_ax_children(node, nodes_by_id, children_by_parent):
            visit(child, depth + 1)

    roots = [n for n in nodes if not n.get("parentId") or n["parentId"] not in nodes_by_id]
    for root in roots:
        visit(root, 0)
    for node in nodes:
        visit(node, 0)

    return "\n".join(lines)


async def eval_str(cdp: CDPClient, sid: str, expression: str) -> str:
    """Evaluate a JavaScript expression and return the result as a string."""
    await cdp.send("Runtime.enable", {}, sid)
    result = await cdp.send(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        sid,
    )
    if result.get("exceptionDetails"):
        exc = result["exceptionDetails"]
        msg = exc.get("text") or (exc.get("exception") or {}).get("description", "Evaluation error")
        raise RuntimeError(msg)
    val = result.get("result", {}).get("value")
    if isinstance(val, dict | list):
        return json.dumps(val, indent=2)
    return str(val) if val is not None else ""


async def shot_str(cdp: CDPClient, sid: str, file_path: str | None = None) -> str:
    """Capture a screenshot and save it. Returns path and coordinate info."""
    # Get device pixel ratio
    dpr = 1.0
    try:
        metrics = await cdp.send("Page.getLayoutMetrics", {}, sid)
        vv = metrics.get("visualViewport", {})
        css_vv = metrics.get("cssVisualViewport", {})
        if vv.get("clientWidth") and css_vv.get("clientWidth"):
            dpr = round(vv["clientWidth"] / css_vv["clientWidth"] * 100) / 100
    except Exception:
        pass

    try:
        result = await cdp.send("Emulation.getDeviceMetricsOverride", {}, sid)
        if result.get("deviceScaleFactor"):
            dpr = result["deviceScaleFactor"]
    except Exception:
        pass

    # Fallback: get DPR from JS
    if dpr == 1.0:
        try:
            raw = await eval_str(cdp, sid, "window.devicePixelRatio")
            parsed = float(raw)
            if parsed > 0:
                dpr = parsed
        except Exception:
            pass

    result = await cdp.send("Page.captureScreenshot", {"format": "png"}, sid)
    out = file_path or "/tmp/screenshot.png"
    Path(out).write_bytes(base64.b64decode(result["data"]))

    lines = [out]
    lines.append(f"Screenshot saved. Device pixel ratio (DPR): {dpr}")
    lines.append("Coordinate mapping:")
    lines.append(f"  Screenshot pixels → CSS pixels (for CDP Input events): divide by {dpr}")
    x_ex = round(100 * dpr)
    y_ex = round(200 * dpr)
    lines.append(
        f"  e.g. screenshot point ({x_ex}, {y_ex}) → CSS (100, 200) → use clickxy <target> 100 200"
    )
    if dpr != 1:
        inv = math.floor(100 / dpr) / 100
        lines.append(
            f"  On this {dpr}x display: CSS px = screenshot px / {dpr} ~= screenshot px * {inv}"
        )
    return "\n".join(lines)


async def html_str(cdp: CDPClient, sid: str, selector: str | None = None) -> str:
    """Get HTML of the page or a specific element."""
    if selector:
        expr = f"document.querySelector({json.dumps(selector)})?.outerHTML || 'Element not found'"
    else:
        expr = "document.documentElement.outerHTML"
    return await eval_str(cdp, sid, expr)


async def wait_for_document_ready(
    cdp: CDPClient, sid: str, timeout_ms: float = NAVIGATION_TIMEOUT
) -> None:
    """Poll document.readyState until 'complete' or timeout."""
    deadline = asyncio.get_event_loop().time() + timeout_ms
    last_state = ""
    last_error: Exception | None = None
    while asyncio.get_event_loop().time() < deadline:
        try:
            state = await eval_str(cdp, sid, "document.readyState")
            last_state = state
            if state == "complete":
                return
        except Exception as e:
            last_error = e
        await asyncio.sleep(0.2)

    if last_state:
        raise RuntimeError(f"Timed out waiting for navigation (last readyState: {last_state})")
    if last_error:
        raise RuntimeError(f"Timed out waiting for navigation to finish ({last_error})")
    raise RuntimeError("Timed out waiting for navigation to finish")


async def nav_str(cdp: CDPClient, sid: str, url: str) -> str:
    """Navigate to a URL and wait for load completion."""
    await cdp.send("Page.enable", {}, sid)
    load_event = cdp.wait_for_event("Page.loadEventFired", NAVIGATION_TIMEOUT)
    result = await cdp.send("Page.navigate", {"url": url}, sid)
    if result.get("errorText"):
        load_event.cancel()
        raise RuntimeError(result["errorText"])
    if result.get("loaderId"):
        await load_event.future
    else:
        load_event.cancel()
    await wait_for_document_ready(cdp, sid, 5.0)
    return f"Navigated to {url}"


async def net_str(cdp: CDPClient, sid: str) -> str:
    """Get network performance entries."""
    raw = await eval_str(
        cdp,
        sid,
        "JSON.stringify(performance.getEntriesByType('resource').map(e => ({"
        "name: e.name.substring(0, 120), type: e.initiatorType,"
        "duration: Math.round(e.duration), size: e.transferSize"
        "})))",
    )
    entries = json.loads(raw)
    lines: list[str] = []
    for e in entries:
        duration = str(e["duration"]).rjust(5)
        size = str(e.get("size") or "?").rjust(8)
        etype = e.get("type", "").ljust(8)
        name = e.get("name", "")
        lines.append(f"{duration}ms  {size}B  {etype}  {name}")
    return "\n".join(lines)


async def click_str(cdp: CDPClient, sid: str, selector: str) -> str:
    """Click an element by CSS selector."""
    if not selector:
        raise RuntimeError("CSS selector required")
    sel_json = json.dumps(selector)
    expr = (
        "(function() {"
        f"  const el = document.querySelector({sel_json});"
        f"  if (!el) return JSON.stringify("
        f"{{ok: false, error: 'Element not found: ' + {sel_json}}});"
        "  el.scrollIntoView({ block: 'center' });"
        "  el.click();"
        "  return JSON.stringify({ok: true, tag: el.tagName,"
        " text: el.textContent.trim().substring(0, 80)});"
        "})()"
    )
    result_str = await eval_str(cdp, sid, expr)
    r = json.loads(result_str)
    if not r.get("ok"):
        raise RuntimeError(r.get("error", "Click failed"))
    return f'Clicked <{r["tag"]}> "{r["text"]}"'


async def click_xy_str(cdp: CDPClient, sid: str, x: str, y: str) -> str:
    """Click at CSS pixel coordinates using Input.dispatchMouseEvent."""
    try:
        cx = float(x)
        cy = float(y)
    except (TypeError, ValueError):
        raise RuntimeError("x and y must be numbers (CSS pixels)") from None
    base = {"x": cx, "y": cy, "button": "left", "clickCount": 1, "modifiers": 0}
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mouseMoved"}, sid)
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mousePressed"}, sid)
    await asyncio.sleep(0.05)
    await cdp.send("Input.dispatchMouseEvent", {**base, "type": "mouseReleased"}, sid)
    return f"Clicked at CSS ({cx}, {cy})"


async def type_str(cdp: CDPClient, sid: str, text: str) -> str:
    """Type text at current focus via Input.insertText."""
    if not text:
        raise RuntimeError("text required")
    await cdp.send("Input.insertText", {"text": text}, sid)
    return f"Typed {len(text)} characters"


async def load_all_str(cdp: CDPClient, sid: str, selector: str, interval_ms: int = 1500) -> str:
    """Repeatedly click a 'load more' button until it disappears."""
    if not selector:
        raise RuntimeError("CSS selector required")
    clicks = 0
    deadline = asyncio.get_event_loop().time() + 5 * 60  # 5-minute hard cap
    interval = interval_ms / 1000.0
    while asyncio.get_event_loop().time() < deadline:
        exists = await eval_str(cdp, sid, f"!!document.querySelector({json.dumps(selector)})")
        if exists != "true":
            break
        click_expr = (
            "(function() {"
            f"  const el = document.querySelector({json.dumps(selector)});"
            "  if (!el) return 'false';"
            "  el.scrollIntoView({ block: 'center' });"
            "  el.click();"
            "  return 'true';"
            "})()"
        )
        clicked = await eval_str(cdp, sid, click_expr)
        if clicked != "true":
            break
        clicks += 1
        await asyncio.sleep(interval)
    return f'Clicked "{selector}" {clicks} time(s) until it disappeared'


async def eval_raw_str(
    cdp: CDPClient, sid: str, method: str, params_json: str | None = None
) -> str:
    """Send a raw CDP command and return the result as JSON."""
    if not method:
        raise RuntimeError('CDP method required (e.g. "DOM.getDocument")')
    params: dict[str, Any] = {}
    if params_json:
        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON params: {params_json}") from None
    result = await cdp.send(method, params, sid)
    return json.dumps(result, indent=2)
