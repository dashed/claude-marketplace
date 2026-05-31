"""Tests for the Sequential Thinking MCP server.

These exercise both the core ``SequentialThinkingServer`` class and the
pydantic-driven argument schema of the registered ``sequentialthinking``
tool, including the JSON-string coercion behavior described in
https://github.com/modelcontextprotocol/servers/issues/3856.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
import types
from typing import Any

import pytest

import mcp_sequential_thinking
from mcp_sequential_thinking import (
    SequentialThinkingServer,
    _detect_color,
    _display_width,
    _process_thought_sync,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> SequentialThinkingServer:
    """A fresh server with thought logging suppressed."""
    monkeypatch.setenv("DISABLE_THOUGHT_LOGGING", "true")
    return SequentialThinkingServer()


@pytest.fixture
def logging_server(monkeypatch: pytest.MonkeyPatch) -> SequentialThinkingServer:
    """A fresh server with thought logging *enabled*."""
    monkeypatch.delenv("DISABLE_THOUGHT_LOGGING", raising=False)
    return SequentialThinkingServer()


# ---------------------------------------------------------------------------
# Valid input tests
# ---------------------------------------------------------------------------


def test_valid_basic_thought(server: SequentialThinkingServer) -> None:
    result = server.process_thought(
        {
            "thought": "This is my first thought",
            "thoughtNumber": 1,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
    )

    assert result["thoughtNumber"] == 1
    assert result["totalThoughts"] == 3
    assert result["nextThoughtNeeded"] is True
    assert result["thoughtHistoryLength"] == 1
    assert result["branches"] == []


def test_thought_with_optional_fields(server: SequentialThinkingServer) -> None:
    result = server.process_thought(
        {
            "thought": "Revising my earlier idea",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
            "isRevision": True,
            "revisesThought": 1,
            "needsMoreThoughts": False,
        }
    )

    assert result["thoughtNumber"] == 2
    assert result["thoughtHistoryLength"] == 1


def test_track_multiple_thoughts(server: SequentialThinkingServer) -> None:
    server.process_thought(
        {
            "thought": "First thought",
            "thoughtNumber": 1,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
    )
    server.process_thought(
        {
            "thought": "Second thought",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
    )
    result = server.process_thought(
        {
            "thought": "Final thought",
            "thoughtNumber": 3,
            "totalThoughts": 3,
            "nextThoughtNeeded": False,
        }
    )

    assert result["thoughtHistoryLength"] == 3
    assert result["nextThoughtNeeded"] is False


def test_auto_adjust_total_thoughts(server: SequentialThinkingServer) -> None:
    result = server.process_thought(
        {
            "thought": "Thought 5",
            "thoughtNumber": 5,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
    )

    assert result["totalThoughts"] == 5
    assert result["thoughtNumber"] == 5


# ---------------------------------------------------------------------------
# Branching tests
# ---------------------------------------------------------------------------


def test_track_two_branches(server: SequentialThinkingServer) -> None:
    server.process_thought(
        {
            "thought": "Main thought",
            "thoughtNumber": 1,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
    )
    server.process_thought(
        {
            "thought": "Branch A thought",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
            "branchFromThought": 1,
            "branchId": "branch-a",
        }
    )
    result = server.process_thought(
        {
            "thought": "Branch B thought",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": False,
            "branchFromThought": 1,
            "branchId": "branch-b",
        }
    )

    assert "branch-a" in result["branches"]
    assert "branch-b" in result["branches"]
    assert len(result["branches"]) == 2
    assert result["thoughtHistoryLength"] == 3


def test_multiple_thoughts_same_branch(server: SequentialThinkingServer) -> None:
    server.process_thought(
        {
            "thought": "Branch thought 1",
            "thoughtNumber": 1,
            "totalThoughts": 2,
            "nextThoughtNeeded": True,
            "branchFromThought": 1,
            "branchId": "branch-a",
        }
    )
    result = server.process_thought(
        {
            "thought": "Branch thought 2",
            "thoughtNumber": 2,
            "totalThoughts": 2,
            "nextThoughtNeeded": False,
            "branchFromThought": 1,
            "branchId": "branch-a",
        }
    )

    assert result["branches"] == ["branch-a"]
    assert len(server.branches["branch-a"]) == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_very_long_thought_string(server: SequentialThinkingServer) -> None:
    result = server.process_thought(
        {
            "thought": "a" * 10000,
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )

    assert result["thoughtNumber"] == 1
    assert result["thoughtHistoryLength"] == 1


def test_single_thought(server: SequentialThinkingServer) -> None:
    result = server.process_thought(
        {
            "thought": "Only thought",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )

    assert result["thoughtNumber"] == 1
    assert result["totalThoughts"] == 1
    assert result["nextThoughtNeeded"] is False


def test_next_thought_needed_false(server: SequentialThinkingServer) -> None:
    result = server.process_thought(
        {
            "thought": "Final thought",
            "thoughtNumber": 3,
            "totalThoughts": 3,
            "nextThoughtNeeded": False,
        }
    )
    assert result["nextThoughtNeeded"] is False


# ---------------------------------------------------------------------------
# Response format
# ---------------------------------------------------------------------------


def test_response_format(server: SequentialThinkingServer) -> None:
    result = server.process_thought(
        {
            "thought": "Test thought",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )

    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "thoughtNumber",
        "totalThoughts",
        "nextThoughtNeeded",
        "branches",
        "thoughtHistoryLength",
    }
    assert isinstance(result["branches"], list)
    assert isinstance(result["thoughtHistoryLength"], int)

    # Must be JSON-serializable
    import json

    json.dumps(result)


def test_process_thought_sync_helper(server: SequentialThinkingServer) -> None:
    result = _process_thought_sync(
        server,
        {
            "thought": "via sync helper",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        },
    )
    assert result["thoughtHistoryLength"] == 1


# ---------------------------------------------------------------------------
# Logging behavior
# ---------------------------------------------------------------------------


def test_disable_thought_logging_suppresses_output(
    server: SequentialThinkingServer,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server.process_thought(
        {
            "thought": "Quiet thought",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    captured = capsys.readouterr()
    assert "Quiet thought" not in captured.err
    assert "💭" not in captured.err


def test_logging_emits_regular_thought(
    logging_server: SequentialThinkingServer,
    capsys: pytest.CaptureFixture[str],
) -> None:
    logging_server.process_thought(
        {
            "thought": "Loud thought",
            "thoughtNumber": 1,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
    )
    captured = capsys.readouterr()
    assert "Loud thought" in captured.err
    assert "💭 Thought 1/3" in captured.err


def test_logging_emits_revision_thought(
    logging_server: SequentialThinkingServer,
    capsys: pytest.CaptureFixture[str],
) -> None:
    logging_server.process_thought(
        {
            "thought": "Revised idea",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
            "isRevision": True,
            "revisesThought": 1,
        }
    )
    captured = capsys.readouterr()
    assert "🔄 Revision 2/3" in captured.err
    assert "revising thought 1" in captured.err


def test_logging_emits_branch_thought(
    logging_server: SequentialThinkingServer,
    capsys: pytest.CaptureFixture[str],
) -> None:
    logging_server.process_thought(
        {
            "thought": "Branch idea",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": False,
            "branchFromThought": 1,
            "branchId": "branch-a",
        }
    )
    captured = capsys.readouterr()
    assert "🌿 Branch 2/3" in captured.err
    assert "from thought 1" in captured.err
    assert "ID: branch-a" in captured.err


def test_disable_thought_logging_case_insensitive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DISABLE_THOUGHT_LOGGING", "TRUE")
    server = SequentialThinkingServer()
    assert server.disable_thought_logging is True

    monkeypatch.setenv("DISABLE_THOUGHT_LOGGING", "True")
    server2 = SequentialThinkingServer()
    assert server2.disable_thought_logging is True

    monkeypatch.setenv("DISABLE_THOUGHT_LOGGING", "false")
    server3 = SequentialThinkingServer()
    assert server3.disable_thought_logging is False


# ---------------------------------------------------------------------------
# String coercion (issue #3856)
# ---------------------------------------------------------------------------
#
# These tests reach into the pydantic argument model that FastMCP synthesizes
# from the @mcp.tool decorated function. Validating raw payloads through that
# model is exactly what FastMCP does when an MCP client invokes the tool, so
# round-tripping JSON-string inputs through it locks in the issue-3856 fix.


def _build_args_model() -> Any:
    """Return the pydantic model FastMCP built for the sequentialthinking tool.

    Reload the module first so we always pick up the current source rather
    than a stale cached registration when the test suite is re-run.
    """
    importlib.reload(mcp_sequential_thinking)
    tool = mcp_sequential_thinking.mcp._tool_manager.get_tool("sequentialthinking")
    assert tool is not None, "sequentialthinking tool was not registered"
    return tool.fn_metadata.arg_model


def test_coercion_string_int_and_bool() -> None:
    model = _build_args_model()
    parsed = model.model_validate(
        {
            "thought": "string-coerced thought",
            "thoughtNumber": "1",
            "totalThoughts": "3",
            "nextThoughtNeeded": "true",
        }
    )
    assert parsed.thoughtNumber == 1
    assert parsed.totalThoughts == 3
    assert parsed.nextThoughtNeeded is True
    assert isinstance(parsed.thoughtNumber, int)
    assert isinstance(parsed.totalThoughts, int)
    assert isinstance(parsed.nextThoughtNeeded, bool)


def test_coercion_string_false() -> None:
    model = _build_args_model()
    parsed = model.model_validate(
        {
            "thought": "done",
            "thoughtNumber": "2",
            "totalThoughts": "2",
            "nextThoughtNeeded": "false",
        }
    )
    assert parsed.nextThoughtNeeded is False


def test_coercion_string_optional_fields() -> None:
    model = _build_args_model()
    parsed = model.model_validate(
        {
            "thought": "revisit",
            "thoughtNumber": "3",
            "totalThoughts": "5",
            "nextThoughtNeeded": "true",
            "isRevision": "true",
            "revisesThought": "1",
            "branchFromThought": "2",
            "branchId": "branch-x",
            "needsMoreThoughts": "false",
        }
    )
    assert parsed.isRevision is True
    assert parsed.revisesThought == 1
    assert parsed.branchFromThought == 2
    assert parsed.branchId == "branch-x"
    assert parsed.needsMoreThoughts is False


def test_coercion_native_types_still_work() -> None:
    model = _build_args_model()
    parsed = model.model_validate(
        {
            "thought": "native types",
            "thoughtNumber": 4,
            "totalThoughts": 5,
            "nextThoughtNeeded": True,
            "isRevision": False,
        }
    )
    assert parsed.thoughtNumber == 4
    assert parsed.totalThoughts == 5
    assert parsed.nextThoughtNeeded is True
    assert parsed.isRevision is False


def test_coercion_case_insensitive_bool_string() -> None:
    model = _build_args_model()
    parsed = model.model_validate(
        {
            "thought": "case",
            "thoughtNumber": "1",
            "totalThoughts": "1",
            "nextThoughtNeeded": "TRUE",
        }
    )
    assert parsed.nextThoughtNeeded is True

    parsed2 = model.model_validate(
        {
            "thought": "case",
            "thoughtNumber": "1",
            "totalThoughts": "1",
            "nextThoughtNeeded": "False",
        }
    )
    assert parsed2.nextThoughtNeeded is False


@pytest.mark.parametrize("value", ["yes", "no", "on", "off", "1", "0", "t", "f"])
def test_coercion_rejects_non_boolean_strings(value: str) -> None:
    """TS zod ``z.boolean()`` only accepts true/false — reject zod-lax forms."""
    from pydantic import ValidationError

    model = _build_args_model()
    with pytest.raises(ValidationError):
        model.model_validate(
            {
                "thought": "reject",
                "thoughtNumber": "1",
                "totalThoughts": "1",
                "nextThoughtNeeded": value,
            }
        )


@pytest.mark.parametrize("value", [0, 1])
def test_coercion_rejects_non_boolean_ints(value: int) -> None:
    """TS zod ``z.boolean()`` rejects numeric 0/1 — so must we."""
    from pydantic import ValidationError

    model = _build_args_model()
    with pytest.raises(ValidationError):
        model.model_validate(
            {
                "thought": "reject",
                "thoughtNumber": "1",
                "totalThoughts": "1",
                "nextThoughtNeeded": value,
            }
        )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1e2", 100), ("1.0", 1), ("0x10", 16)],
)
def test_coercion_accepts_scientific_and_float_strings(raw: str, expected: int) -> None:
    """Match TS zod ``z.coerce.number().int()`` breadth on string inputs."""
    model = _build_args_model()
    parsed = model.model_validate(
        {
            "thought": "widen",
            "thoughtNumber": raw,
            "totalThoughts": "1",
            "nextThoughtNeeded": "false",
        }
    )
    assert parsed.thoughtNumber == expected
    assert isinstance(parsed.thoughtNumber, int)


def test_coercion_accepts_native_integer_float() -> None:
    """A float whose value is an integer (``1.0``) must coerce to ``1``."""
    model = _build_args_model()
    parsed = model.model_validate(
        {
            "thought": "float-int",
            "thoughtNumber": 1.0,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    assert parsed.thoughtNumber == 1
    assert isinstance(parsed.thoughtNumber, int)


def test_coercion_rejects_non_integer_float() -> None:
    """Non-integer floats must fail validation."""
    from pydantic import ValidationError

    model = _build_args_model()
    with pytest.raises(ValidationError):
        model.model_validate(
            {
                "thought": "non-int-float",
                "thoughtNumber": 1.5,
                "totalThoughts": 1,
                "nextThoughtNeeded": False,
            }
        )


# ---------------------------------------------------------------------------
# Wrapping / multi-line rendering
# ---------------------------------------------------------------------------


def _make_render_server(
    monkeypatch: pytest.MonkeyPatch,
    *,
    use_color: bool = False,
    max_content_width: int | None = 40,
) -> SequentialThinkingServer:
    """Build a server that actually logs, with a deterministic box width."""
    monkeypatch.delenv("DISABLE_THOUGHT_LOGGING", raising=False)
    return SequentialThinkingServer(
        use_color=use_color, max_content_width=max_content_width
    )


def _box_content_rows(stderr: str) -> list[str]:
    """Return the raw content rows (between the mid divider and bottom border)."""
    lines = stderr.split("\n")
    mid = next((i for i, line in enumerate(lines) if line.startswith("├")), None)
    bot = next((i for i, line in enumerate(lines) if line.startswith("└")), None)
    assert mid is not None and bot is not None, f"box borders missing: {stderr!r}"
    return lines[mid + 1 : bot]


def test_multiline_thought_preserves_line_breaks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch)
    server.process_thought(
        {
            "thought": "line one\nline two\nline three",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    err = capsys.readouterr().err
    assert "line one" in err
    assert "line two" in err
    assert "line three" in err

    rows = _box_content_rows(err)
    assert len(rows) >= 3
    # Each of the three inputs should live on its own row.
    joined_rows = "\n".join(rows)
    assert joined_rows.count("line one") == 1
    assert joined_rows.count("line two") == 1
    assert joined_rows.count("line three") == 1


def test_long_thought_wraps_at_max_width(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch)
    server.process_thought(
        {
            "thought": "x" * 500,
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    err = capsys.readouterr().err
    lines = [line for line in err.split("\n") if line]

    for line in lines:
        assert len(line) <= 44, f"line overflows box: {line!r} ({len(line)} chars)"

    rows = _box_content_rows(err)
    assert len(rows) >= 12, f"expected >=12 wrapped rows, got {len(rows)}"

    top = next(line for line in lines if line.startswith("┌"))
    bottom = next(line for line in lines if line.startswith("└"))
    assert len(top) == len(bottom)


def test_long_thought_with_spaces_wraps_at_word_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prose = (
        "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do "
        "eiusmod tempor incididunt ut labore et dolore magna aliqua ut "
        "enim ad minim veniam quis nostrud exercitation ullamco laboris "
        "nisi ut aliquip ex ea commodo consequat duis aute irure dolor "
        "in reprehenderit in voluptate velit esse cillum"
    )
    assert len(prose) >= 280

    server = _make_render_server(monkeypatch)
    server.process_thought(
        {
            "thought": prose,
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    err = capsys.readouterr().err

    rows = _box_content_rows(err)
    for row in rows:
        assert len(row) <= 44

    content_text = " ".join(row.strip("│").strip() for row in rows)
    for word in prose.split():
        assert word in content_text.split(), (
            f"word {word!r} missing or split across rows"
        )


def test_empty_thought_renders_empty_row(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch)
    server.process_thought(
        {
            "thought": "",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    err = capsys.readouterr().err

    # Output is "\n<top>\n<header>\n<mid>\n<empty>\n<bottom>\n"
    lines = err.split("\n")
    # Leading "\n" gives an empty first element.
    assert lines[0] == ""
    assert lines[1].startswith("┌") and lines[1].endswith("┐")
    assert lines[2].startswith("│") and "💭 Thought 1/1" in lines[2]
    assert lines[3].startswith("├") and lines[3].endswith("┤")
    assert lines[4].startswith("│") and lines[4].endswith("│")
    # Empty content row: nothing between the borders except padding spaces.
    assert lines[4].strip("│").strip() == ""
    assert lines[5].startswith("└") and lines[5].endswith("┘")

    rows = _box_content_rows(err)
    assert len(rows) == 1


def test_paragraph_break_preserved(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch)
    server.process_thought(
        {
            "thought": "first paragraph\n\nsecond paragraph",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    err = capsys.readouterr().err
    rows = _box_content_rows(err)
    assert len(rows) == 3
    assert "first paragraph" in rows[0]
    assert rows[1].strip("│").strip() == ""
    assert "second paragraph" in rows[2]


def test_box_borders_consistent_width(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch)
    server.process_thought(
        {
            "thought": "short\na much longer line than the first one\ntiny",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    err = capsys.readouterr().err
    lines = [line for line in err.split("\n") if line]

    top = next(line for line in lines if line.startswith("┌"))
    mid = next(line for line in lines if line.startswith("├"))
    bot = next(line for line in lines if line.startswith("└"))
    assert len(top) == len(mid) == len(bot)


@pytest.mark.parametrize(
    ("kwargs", "expected_emoji"),
    [
        ({}, "💭"),
        ({"isRevision": True, "revisesThought": 1}, "🔄"),
        ({"branchFromThought": 1, "branchId": "alt"}, "🌿"),
    ],
)
def test_header_with_emoji_does_not_overflow_border(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    kwargs: dict[str, Any],
    expected_emoji: str,
) -> None:
    """Regression: emoji in header are East Asian Wide (2 cells), not 1.

    ``len()`` / ``str.ljust`` both count code points, so the old
    implementation produced a header row that was exactly 1 display cell
    wider than the border. Every rendered line must now have the same
    terminal-cell width.
    """
    server = _make_render_server(monkeypatch)
    payload: dict[str, Any] = {
        "thought": "Short thought body.",
        "thoughtNumber": 1,
        "totalThoughts": 1,
        "nextThoughtNeeded": False,
    }
    payload.update(kwargs)
    server.process_thought(payload)

    err = capsys.readouterr().err
    box_lines = [line for line in err.split("\n") if line]
    # Sanity: the header actually contains the emoji we expect.
    assert any(expected_emoji in line for line in box_lines)

    widths = {_display_width(line) for line in box_lines}
    assert len(widths) == 1, (
        f"ragged box: lines have mixed display widths {widths}\n"
        + "\n".join(f"{_display_width(line):>3}  {line}" for line in box_lines)
    )


# ---------------------------------------------------------------------------
# Color gating
# ---------------------------------------------------------------------------


def test_no_color_when_use_color_false(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch, use_color=False)
    server.process_thought(
        {
            "thought": "plain thought",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": False,
        }
    )
    err = capsys.readouterr().err
    assert "\x1b[" not in err


def test_color_when_use_color_true_regular_thought(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch, use_color=True)
    server.process_thought(
        {
            "thought": "blue thought",
            "thoughtNumber": 1,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
        }
    )
    err = capsys.readouterr().err
    assert "\x1b[34m" in err
    assert "\x1b[0m" in err
    assert "💭 Thought 1/3" in err


def test_color_revision_uses_yellow(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch, use_color=True)
    server.process_thought(
        {
            "thought": "reconsidered",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
            "isRevision": True,
            "revisesThought": 1,
        }
    )
    err = capsys.readouterr().err
    assert "\x1b[33m" in err
    assert "\x1b[34m" not in err
    assert "🔄 Revision 2/3" in err


def test_color_branch_uses_green(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = _make_render_server(monkeypatch, use_color=True)
    server.process_thought(
        {
            "thought": "branching out",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
            "branchFromThought": 1,
            "branchId": "alt",
        }
    )
    err = capsys.readouterr().err
    assert "\x1b[32m" in err
    assert "\x1b[34m" not in err
    assert "\x1b[33m" not in err
    assert "🌿 Branch 2/3" in err


def test_detect_color_respects_no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORCE_COLOR", raising=False)

    monkeypatch.setenv("NO_COLOR", "")
    assert _detect_color() is False

    monkeypatch.setenv("NO_COLOR", "1")
    assert _detect_color() is False


def test_detect_color_respects_force_color(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)

    monkeypatch.setenv("FORCE_COLOR", "1")
    assert _detect_color() is True

    # FORCE_COLOR=0 is explicitly NOT a force — it falls through to TTY
    # detection. Pin isatty to False so the fallback is deterministic and we
    # can confirm "0" does not force-enable colors.
    monkeypatch.setenv("FORCE_COLOR", "0")
    fake_stderr = types.SimpleNamespace(isatty=lambda: False)
    monkeypatch.setattr(sys, "stderr", fake_stderr)
    assert _detect_color() is False


def test_detect_color_tty_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)

    monkeypatch.setattr(sys, "stderr", types.SimpleNamespace(isatty=lambda: True))
    assert _detect_color() is True

    monkeypatch.setattr(sys, "stderr", types.SimpleNamespace(isatty=lambda: False))
    assert _detect_color() is False


# ---------------------------------------------------------------------------
# Tool registration metadata (title + annotations)
# ---------------------------------------------------------------------------
#
# Mirrors the `title` and `annotations` fields set by the TypeScript reference
# server in sequentialthinking/index.ts. Locks in fidelity with that server so
# clients see the same read-only/non-destructive/idempotent/closed-world hints.


def test_tool_has_title_and_annotations() -> None:
    importlib.reload(mcp_sequential_thinking)
    tool = mcp_sequential_thinking.mcp._tool_manager.get_tool("sequentialthinking")
    assert tool is not None

    annotations = tool.annotations
    assert annotations is not None
    assert annotations.title == "Sequential Thinking"
    assert annotations.readOnlyHint is True
    assert annotations.destructiveHint is False
    assert annotations.idempotentHint is True
    assert annotations.openWorldHint is False


# ---------------------------------------------------------------------------
# Server name (initialize handshake)
# ---------------------------------------------------------------------------
#
# The TypeScript reference server advertises `serverInfo.name =
# "sequential-thinking-server"` in its initialize handshake
# (sequentialthinking/index.ts). Lock the Python port to the same name so
# clients identifying servers by name see parity.


def test_server_name_matches_ts_reference() -> None:
    importlib.reload(mcp_sequential_thinking)
    assert mcp_sequential_thinking.mcp.name == "sequential-thinking-server"


# ---------------------------------------------------------------------------
# Field descriptions (TS-parity, issue #3856 hints)
# ---------------------------------------------------------------------------
#
# The TS reference server phrases thoughtNumber/totalThoughts descriptions as
# "numeric value, e.g., ..." as a deliberate hint to string-coercing clients
# (see mcp-anthropic-servers/src/sequentialthinking/index.ts). Lock the
# Python port to the same phrasing.


def test_tool_field_descriptions_match_ts() -> None:
    model = _build_args_model()
    assert (
        model.model_fields["thoughtNumber"].description
        == "Current thought number (numeric value, e.g., 1, 2, 3)"
    )
    assert (
        model.model_fields["totalThoughts"].description
        == "Estimated total thoughts needed (numeric value, e.g., 5, 10)"
    )


# ---------------------------------------------------------------------------
# Error body shape on uncaught exception (TS parity)
# ---------------------------------------------------------------------------
#
# The TS reference server returns ``{"error": ..., "status": "failed"}`` when
# ``processThought`` throws. The Python tool wraps its body in try/except so
# MCP clients that ``json.loads`` the content text see the same body shape.


def test_tool_returns_ts_error_shape_on_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mcp_sequential_thinking._thinking_server,
        "process_thought",
        lambda _input: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = asyncio.run(
        mcp_sequential_thinking.sequentialthinking(
            thought="will fail",
            nextThoughtNeeded=False,
            thoughtNumber=1,
            totalThoughts=1,
        )
    )

    assert result == {"error": "boom", "status": "failed"}


# ---------------------------------------------------------------------------
# Branch tracking requires BOTH branchFromThought AND branchId
# ---------------------------------------------------------------------------
#
# The TS reference server only registers a branch when both fields are
# present (sequentialthinking/lib.ts). Lock the invariant in the Python port
# (mcp_sequential_thinking.py:289–292) so half-specified inputs silently
# no-op rather than creating orphan/phantom branches.


def test_branch_not_tracked_without_branch_id(
    server: SequentialThinkingServer,
) -> None:
    result = server.process_thought(
        {
            "thought": "pseudo-branch without id",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
            "branchFromThought": 1,
        }
    )
    assert result["branches"] == []
    assert server.branches == {}


def test_branch_not_tracked_without_branch_from(
    server: SequentialThinkingServer,
) -> None:
    result = server.process_thought(
        {
            "thought": "pseudo-branch without from",
            "thoughtNumber": 2,
            "totalThoughts": 3,
            "nextThoughtNeeded": True,
            "branchId": "orphan-branch",
        }
    )
    assert result["branches"] == []
    assert server.branches == {}
