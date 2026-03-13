"""Tests for chrome_cdp.commands — command implementations."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from chrome_cdp.commands import (
    click_str,
    click_xy_str,
    eval_raw_str,
    eval_str,
    format_ax_node,
    format_page_list,
    html_str,
    load_all_str,
    nav_str,
    net_str,
    ordered_ax_children,
    shot_str,
    should_show_ax_node,
    snapshot_str,
    type_str,
)

# ── format_page_list ───────────────────────────────────────────────────────


class TestFormatPageList:
    def test_basic_formatting(self, sample_pages):
        result = format_page_list(sample_pages)
        lines = result.split("\n")
        assert len(lines) == 3
        # Each line should contain the target prefix, title, and URL
        assert "Example Page" in lines[0]
        assert "https://example.com" in lines[0]

    def test_empty_list(self):
        result = format_page_list([])
        assert result == ""

    def test_single_page(self):
        pages = [{"targetId": "ABCD1234", "title": "Only Page", "url": "https://only.com"}]
        result = format_page_list(pages)
        assert "Only Page" in result
        assert "https://only.com" in result

    def test_long_title_truncated(self):
        pages = [{"targetId": "ABCD1234", "title": "X" * 100, "url": "https://test.com"}]
        result = format_page_list(pages)
        # Title is truncated to 54 chars
        # The formatted line shouldn't contain 100 X's
        assert "X" * 55 not in result

    def test_missing_title_and_url(self):
        pages = [{"targetId": "ABCD1234"}]
        result = format_page_list(pages)
        assert "ABCD1234" in result


# ── should_show_ax_node ────────────────────────────────────────────────────


class TestShouldShowAxNode:
    def test_show_named_node(self):
        node = {"role": {"value": "heading"}, "name": {"value": "Title"}}
        assert should_show_ax_node(node) is True

    def test_hide_generic_role(self):
        node = {"role": {"value": "generic"}, "name": {"value": "something"}}
        assert should_show_ax_node(node) is False

    def test_hide_none_role(self):
        node = {"role": {"value": "none"}, "name": {"value": "something"}}
        assert should_show_ax_node(node) is False

    def test_hide_empty_name_no_value(self):
        node = {"role": {"value": "div"}, "name": {"value": ""}}
        assert should_show_ax_node(node) is False

    def test_hide_empty_name_empty_value(self):
        node = {"role": {"value": "div"}, "name": {"value": ""}, "value": {"value": ""}}
        assert should_show_ax_node(node) is False

    def test_show_empty_name_with_value(self):
        node = {"role": {"value": "textbox"}, "name": {"value": ""}, "value": {"value": "hello"}}
        assert should_show_ax_node(node) is True

    def test_compact_hides_inline_text_box(self):
        node = {"role": {"value": "InlineTextBox"}, "name": {"value": "text"}}
        assert should_show_ax_node(node, compact=True) is False

    def test_non_compact_shows_inline_text_box(self):
        node = {"role": {"value": "InlineTextBox"}, "name": {"value": "text"}}
        assert should_show_ax_node(node, compact=False) is True

    def test_missing_role_with_name(self):
        node = {"name": {"value": "test"}}
        # role is missing → empty string (not "none"/"generic"), name is non-empty → shown
        assert should_show_ax_node(node) is True

    def test_missing_role_no_name(self):
        node = {}
        # No role, no name → empty name with no value → hidden
        assert should_show_ax_node(node) is False

    def test_missing_name(self):
        node = {"role": {"value": "button"}}
        # name is None → returns False (empty name, no value)
        assert should_show_ax_node(node) is False


# ── format_ax_node ─────────────────────────────────────────────────────────


class TestFormatAxNode:
    def test_basic_format(self):
        node = {"role": {"value": "heading"}, "name": {"value": "Title"}}
        result = format_ax_node(node, 0)
        assert result == "[heading] Title"

    def test_with_value(self):
        node = {
            "role": {"value": "link"},
            "name": {"value": "Click"},
            "value": {"value": "https://example.com"},
        }
        result = format_ax_node(node, 0)
        assert result == '[link] Click = "https://example.com"'

    def test_indentation(self):
        node = {"role": {"value": "button"}, "name": {"value": "OK"}}
        result = format_ax_node(node, 3)
        assert result == "      [button] OK"

    def test_max_indentation_capped(self):
        node = {"role": {"value": "item"}, "name": {"value": "deep"}}
        result = format_ax_node(node, 15)
        # Capped at depth 10 → 20 spaces
        assert result.startswith("  " * 10)

    def test_empty_name(self):
        node = {"role": {"value": "div"}, "name": {"value": ""}, "value": {"value": "val"}}
        result = format_ax_node(node, 0)
        assert result == '[div] = "val"'

    def test_no_name_no_value(self):
        node = {"role": {"value": "group"}, "name": {"value": ""}}
        result = format_ax_node(node, 0)
        assert result == "[group]"

    def test_numeric_value(self):
        node = {"role": {"value": "slider"}, "name": {"value": "Volume"}, "value": {"value": 50}}
        result = format_ax_node(node, 0)
        assert result == "[slider] Volume = 50"


# ── ordered_ax_children ────────────────────────────────────────────────────


class TestOrderedAxChildren:
    def test_children_from_child_ids(self):
        parent = {"nodeId": "1", "childIds": ["2", "3"]}
        child2 = {"nodeId": "2"}
        child3 = {"nodeId": "3"}
        nodes_by_id = {"2": child2, "3": child3}
        children_by_parent: dict[str, list[dict[str, Any]]] = {}

        result = ordered_ax_children(parent, nodes_by_id, children_by_parent)
        assert result == [child2, child3]

    def test_children_from_parent_map(self):
        parent = {"nodeId": "1", "childIds": []}
        child2 = {"nodeId": "2"}
        nodes_by_id: dict[str, dict[str, Any]] = {}
        children_by_parent = {"1": [child2]}

        result = ordered_ax_children(parent, nodes_by_id, children_by_parent)
        assert result == [child2]

    def test_deduplicates(self):
        parent = {"nodeId": "1", "childIds": ["2"]}
        child2 = {"nodeId": "2"}
        nodes_by_id = {"2": child2}
        children_by_parent = {"1": [child2]}

        result = ordered_ax_children(parent, nodes_by_id, children_by_parent)
        # Child 2 appears in both sources but should only appear once
        assert len(result) == 1
        assert result[0] is child2

    def test_missing_child_id(self):
        parent = {"nodeId": "1", "childIds": ["2", "999"]}
        child2 = {"nodeId": "2"}
        nodes_by_id = {"2": child2}
        children_by_parent: dict[str, list[dict[str, Any]]] = {}

        result = ordered_ax_children(parent, nodes_by_id, children_by_parent)
        assert result == [child2]

    def test_no_children(self):
        parent = {"nodeId": "1", "childIds": []}
        result = ordered_ax_children(parent, {}, {})
        assert result == []

    def test_no_child_ids_key(self):
        parent = {"nodeId": "1"}
        result = ordered_ax_children(parent, {}, {})
        assert result == []


# ── eval_str ───────────────────────────────────────────────────────────────


def make_cdp_mock(**send_return: Any) -> AsyncMock:
    """Create a mock CDPClient with a configured send return value."""
    cdp = AsyncMock()
    cdp.send = AsyncMock(return_value=send_return.get("value", {}))
    return cdp


class TestEvalStr:
    async def test_simple_value(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Runtime.enable
                {"result": {"value": 42}},  # Runtime.evaluate
            ]
        )
        result = await eval_str(cdp, "sid", "1 + 1")
        assert result == "42"

    async def test_string_value(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Runtime.enable
                {"result": {"value": "hello"}},  # Runtime.evaluate
            ]
        )
        result = await eval_str(cdp, "sid", '"hello"')
        assert result == "hello"

    async def test_none_value(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Runtime.enable
                {"result": {}},  # Runtime.evaluate — no value key
            ]
        )
        result = await eval_str(cdp, "sid", "undefined")
        assert result == ""

    async def test_dict_value_formatted_as_json(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,
                {"result": {"value": {"key": "val"}}},
            ]
        )
        result = await eval_str(cdp, "sid", '({key: "val"})')
        parsed = json.loads(result)
        assert parsed == {"key": "val"}

    async def test_list_value_formatted_as_json(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,
                {"result": {"value": [1, 2, 3]}},
            ]
        )
        result = await eval_str(cdp, "sid", "[1,2,3]")
        assert json.loads(result) == [1, 2, 3]

    async def test_exception_details_text(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,
                {"exceptionDetails": {"text": "SyntaxError: unexpected"}},
            ]
        )
        with pytest.raises(RuntimeError, match="SyntaxError: unexpected"):
            await eval_str(cdp, "sid", "bad syntax {{")

    async def test_exception_details_description(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,
                {
                    "exceptionDetails": {
                        "exception": {"description": "ReferenceError: x is not defined"}
                    }
                },
            ]
        )
        with pytest.raises(RuntimeError, match="ReferenceError"):
            await eval_str(cdp, "sid", "x")


# ── shot_str ───────────────────────────────────────────────────────────────


class TestShotStr:
    async def test_saves_screenshot(self, tmp_path):
        png_data = base64.b64encode(b"fake png data").decode()
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                # Page.getLayoutMetrics
                {
                    "visualViewport": {"clientWidth": 1920},
                    "cssVisualViewport": {"clientWidth": 960},
                },
                # Emulation.getDeviceMetricsOverride — raise to skip
                Exception("not set"),
                # Page.captureScreenshot
                {"data": png_data},
            ]
        )
        # Second call raises, handle that
        cdp.send = AsyncMock()
        call_count = 0

        async def multi_send(method, params=None, sid=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if method == "Page.getLayoutMetrics":
                return {
                    "visualViewport": {"clientWidth": 1920},
                    "cssVisualViewport": {"clientWidth": 960},
                }
            if method == "Emulation.getDeviceMetricsOverride":
                raise RuntimeError("not set")
            if method == "Page.captureScreenshot":
                return {"data": png_data}
            if method == "Runtime.enable":
                return None
            if method == "Runtime.evaluate":
                return {"result": {"value": 2.0}}
            return {}

        cdp.send = AsyncMock(side_effect=multi_send)

        out_file = str(tmp_path / "test_shot.png")
        result = await shot_str(cdp, "sid", out_file)

        assert out_file in result
        assert "DPR" in result
        assert Path(out_file).read_bytes() == b"fake png data"

    async def test_default_path(self):
        png_data = base64.b64encode(b"data").decode()

        async def multi_send(method, params=None, sid=None, **kwargs):
            if method == "Page.getLayoutMetrics":
                return {"visualViewport": {}, "cssVisualViewport": {}}
            if method == "Emulation.getDeviceMetricsOverride":
                raise RuntimeError("not set")
            if method == "Page.captureScreenshot":
                return {"data": png_data}
            if method == "Runtime.enable":
                return None
            if method == "Runtime.evaluate":
                return {"result": {"value": 1.0}}
            return {}

        cdp = AsyncMock()
        cdp.send = AsyncMock(side_effect=multi_send)

        with patch.object(Path, "write_bytes"):
            result = await shot_str(cdp, "sid")
            assert "/tmp/screenshot.png" in result


# ── html_str ───────────────────────────────────────────────────────────────


class TestHtmlStr:
    async def test_full_page(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Runtime.enable
                {"result": {"value": "<html><body>Hello</body></html>"}},
            ]
        )
        result = await html_str(cdp, "sid")
        assert result == "<html><body>Hello</body></html>"

    async def test_with_selector(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Runtime.enable
                {"result": {"value": "<div>Found</div>"}},
            ]
        )
        result = await html_str(cdp, "sid", selector="#main")
        assert result == "<div>Found</div>"
        # Verify the expression includes the selector
        call_args = cdp.send.call_args_list[1]
        expr = call_args[0][1]["expression"]
        assert "#main" in expr


# ── nav_str ────────────────────────────────────────────────────────────────


class TestNavStr:
    async def test_successful_navigation(self):
        cdp = AsyncMock()

        # Track the wait_for_event call
        import asyncio

        from chrome_cdp.client import EventWaiter

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        fut.set_result({"timestamp": 123})

        cdp.wait_for_event = lambda *a, **kw: EventWaiter(future=fut)
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Page.enable
                {"loaderId": "loader-1"},  # Page.navigate
                None,  # Runtime.enable (from eval_str in wait_for_document_ready)
                {"result": {"value": "complete"}},  # Runtime.evaluate
            ]
        )

        result = await nav_str(cdp, "sid", "https://example.com")
        assert "Navigated to https://example.com" in result

    async def test_navigation_error(self):
        cdp = AsyncMock()

        import asyncio

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        waiter_cancelled = False

        def cancel():
            nonlocal waiter_cancelled
            waiter_cancelled = True

        from chrome_cdp.client import EventWaiter

        waiter = EventWaiter(future=fut, _cancel=cancel)
        cdp.wait_for_event = lambda *a, **kw: waiter
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Page.enable
                {"errorText": "net::ERR_NAME_NOT_RESOLVED"},  # Page.navigate
            ]
        )

        with pytest.raises(RuntimeError, match="net::ERR_NAME_NOT_RESOLVED"):
            await nav_str(cdp, "sid", "https://nonexistent.example")
        assert waiter_cancelled


# ── click_str ──────────────────────────────────────────────────────────────


class TestClickStr:
    async def test_successful_click(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Runtime.enable
                {"result": {"value": json.dumps({"ok": True, "tag": "BUTTON", "text": "Submit"})}},
            ]
        )
        result = await click_str(cdp, "sid", "#submit-btn")
        assert result == 'Clicked <BUTTON> "Submit"'

    async def test_element_not_found(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,
                {
                    "result": {
                        "value": json.dumps({"ok": False, "error": "Element not found: #missing"})
                    }
                },
            ]
        )
        with pytest.raises(RuntimeError, match="Element not found"):
            await click_str(cdp, "sid", "#missing")

    async def test_empty_selector_raises(self):
        cdp = AsyncMock()
        with pytest.raises(RuntimeError, match="CSS selector required"):
            await click_str(cdp, "sid", "")


# ── click_xy_str ───────────────────────────────────────────────────────────


class TestClickXyStr:
    async def test_successful_click(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(return_value={})
        result = await click_xy_str(cdp, "sid", "100", "200")
        assert result == "Clicked at CSS (100.0, 200.0)"
        # Should have 3 sends: mouseMoved, mousePressed, mouseReleased
        assert cdp.send.call_count == 3

    async def test_float_coordinates(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(return_value={})
        result = await click_xy_str(cdp, "sid", "100.5", "200.7")
        assert "100.5" in result
        assert "200.7" in result

    async def test_invalid_coordinates(self):
        cdp = AsyncMock()
        with pytest.raises(RuntimeError, match="x and y must be numbers"):
            await click_xy_str(cdp, "sid", "abc", "200")


# ── type_str ───────────────────────────────────────────────────────────────


class TestTypeStr:
    async def test_type_text(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(return_value={})
        result = await type_str(cdp, "sid", "hello world")
        assert result == "Typed 11 characters"

    async def test_empty_text_raises(self):
        cdp = AsyncMock()
        with pytest.raises(RuntimeError, match="text required"):
            await type_str(cdp, "sid", "")


# ── load_all_str ───────────────────────────────────────────────────────────


class TestLoadAllStr:
    async def test_clicks_until_gone(self):
        cdp = AsyncMock()
        call_count = 0

        async def mock_send(method, params=None, sid=None, **kwargs):
            nonlocal call_count
            if method == "Runtime.enable":
                return None
            if method == "Runtime.evaluate":
                call_count += 1
                expr = params.get("expression", "")
                # First two exist checks return true, then false
                if "!!" in expr:
                    if call_count <= 4:  # exists check: calls 1, 3 (enable skipped after first)
                        return {"result": {"value": "true"}}
                    return {"result": {"value": "false"}}
                # Click expression
                return {"result": {"value": "true"}}
            return {}

        cdp.send = AsyncMock(side_effect=mock_send)
        result = await load_all_str(cdp, "sid", ".load-more", interval_ms=10)
        assert "load-more" in result
        assert "time(s)" in result

    async def test_empty_selector_raises(self):
        cdp = AsyncMock()
        with pytest.raises(RuntimeError, match="CSS selector required"):
            await load_all_str(cdp, "sid", "")


# ── eval_raw_str ───────────────────────────────────────────────────────────


class TestEvalRawStr:
    async def test_basic_command(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(return_value={"root": {"nodeId": 1}})
        result = await eval_raw_str(cdp, "sid", "DOM.getDocument", "{}")
        parsed = json.loads(result)
        assert parsed == {"root": {"nodeId": 1}}

    async def test_no_params(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(return_value={"result": "ok"})
        result = await eval_raw_str(cdp, "sid", "Page.reload")
        parsed = json.loads(result)
        assert parsed == {"result": "ok"}

    async def test_empty_method_raises(self):
        cdp = AsyncMock()
        with pytest.raises(RuntimeError, match="CDP method required"):
            await eval_raw_str(cdp, "sid", "")

    async def test_invalid_json_params_raises(self):
        cdp = AsyncMock()
        with pytest.raises(RuntimeError, match="Invalid JSON params"):
            await eval_raw_str(cdp, "sid", "DOM.getDocument", "not-json")


# ── net_str ────────────────────────────────────────────────────────────────


class TestNetStr:
    async def test_formats_entries(self):
        entries = [
            {
                "name": "https://example.com/script.js",
                "type": "script",
                "duration": 120,
                "size": 5432,
            },
            {
                "name": "https://example.com/style.css",
                "type": "link",
                "duration": 45,
                "size": 1234,
            },
        ]
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,  # Runtime.enable
                {"result": {"value": json.dumps(entries)}},
            ]
        )
        result = await net_str(cdp, "sid")
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert "120ms" in lines[0]
        assert "5432B" in lines[0]
        assert "script" in lines[0]

    async def test_empty_entries(self):
        cdp = AsyncMock()
        cdp.send = AsyncMock(
            side_effect=[
                None,
                {"result": {"value": "[]"}},
            ]
        )
        result = await net_str(cdp, "sid")
        assert result == ""


# ── snapshot_str ───────────────────────────────────────────────────────────


class TestSnapshotStr:
    async def test_basic_snapshot(self, sample_ax_nodes):
        cdp = AsyncMock()
        cdp.send = AsyncMock(return_value={"nodes": sample_ax_nodes})

        result = await snapshot_str(cdp, "sid", compact=True)

        # Should contain RootWebArea, heading, link but not generic/none
        assert "[RootWebArea]" in result
        assert "[heading]" in result
        assert "[link]" in result
        assert "[generic]" not in result
        assert "[none]" not in result
