#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=0.1.0"]
#
# [project.optional-dependencies]
# dev = ["pytest>=7.0", "pytest-asyncio>=0.21.0"]
# ///
"""
`mcp_sequential_thinking.py` – **Model Context Protocol** server for dynamic,
reflective problem-solving via a single `sequentialthinking` tool.

This server is a Python port of the official TypeScript ``sequential-thinking``
MCP server. It exposes one tool that lets a model record an evolving chain of
thoughts, branch off to explore alternatives, revise earlier steps, and adjust
the planned thought count on the fly. The server keeps the running history in
memory for the lifetime of the process.

Tool exposed to LLMs
--------------------
* **`sequentialthinking`** – Record one step in an iterative thinking process.

Environment variables
---------------------
* ``DISABLE_THOUGHT_LOGGING`` – When set (case-insensitive) to ``"true"``, the
  server suppresses the formatted thought box that is otherwise written to
  stderr. All other behavior is unchanged.

String coercion (issue #3856)
-----------------------------
Some MCP clients (notably Claude Code) serialize numeric and boolean tool
arguments as JSON strings. The original npm-released TypeScript server
rejects those payloads. This Python port deliberately accepts BOTH the
native Python type AND a coercible string for every numeric/boolean
parameter, using pydantic ``BeforeValidator`` annotations:

* Booleans: only the native ``bool`` and the case-insensitive strings
  ``"true"``/``"false"`` (with surrounding whitespace stripped) are
  accepted. Numeric ``0``/``1``, ``"yes"``/``"no"``, ``"on"``/``"off"``,
  and similar forms are rejected to match TS zod ``z.boolean()`` strictness.
* Integers: native ``int``, integer-valued ``float``, and strings parseable
  as decimal (``"1"``), base-prefixed (``"0x10"``), scientific notation
  (``"1e2"``), or explicit float (``"1.0"``) — matching TS zod
  ``z.coerce.number().int()`` breadth. Non-integer floats/strings fall
  through to pydantic, which rejects them.

Quick start
-----------
```bash
chmod +x mcp_sequential_thinking.py

# Run as MCP server (stdio transport)
./mcp_sequential_thinking.py

# Run with thought logging suppressed
DISABLE_THOUGHT_LOGGING=true ./mcp_sequential_thinking.py
```
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import textwrap
import unicodedata
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BeforeValidator, Field

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# String → native coercion helpers (for issue #3856)
# ---------------------------------------------------------------------------


def _coerce_bool(value: Any) -> Any:
    """Coerce JSON-string booleans to Python bools.

    Accepts the native ``bool`` unchanged and converts the strings ``"true"``
    and ``"false"`` (case-insensitive, surrounding whitespace stripped) to
    their Python equivalents. Any other value — including numeric ``0``/``1``,
    ``"yes"``/``"no"``, ``"on"``/``"off"`` — raises ``ValueError`` so pydantic
    reports validation failure. This matches the TS reference server's
    ``z.boolean()`` semantics, which only accept native booleans.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise ValueError(
            f"Cannot coerce string {value!r} to bool; expected 'true' or 'false'"
        )
    raise ValueError(
        f"Cannot coerce {type(value).__name__} to bool; "
        "expected bool or 'true'/'false' string"
    )


def _coerce_int(value: Any) -> Any:
    """Coerce JSON-string and float integers to Python ints.

    Accepts the native ``int`` unchanged. A non-empty string is parsed via
    ``int(stripped, 0)`` (so decimal as well as ``0x10``/``0b11``/``0o17``
    literals work); if that fails, the string is re-parsed via ``float`` and
    accepted when the result is integer-valued (covers ``"1.0"``, ``"1e2"``).
    Native ``float`` values are likewise accepted when integer-valued. Native
    ``bool`` is explicitly passed through so pydantic can reject it — otherwise
    ``True``/``False`` would silently coerce to ``1``/``0``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return value
        try:
            return int(stripped, 0)
        except ValueError:
            pass
        try:
            parsed = float(stripped)
        except ValueError:
            return value
        if parsed.is_integer():
            return int(parsed)
        return value
    return value


CoercedBool = Annotated[bool, BeforeValidator(_coerce_bool)]
CoercedInt = Annotated[int, BeforeValidator(_coerce_int)]
OptionalCoercedBool = Annotated[bool | None, BeforeValidator(_coerce_bool)]
OptionalCoercedInt = Annotated[int | None, BeforeValidator(_coerce_int)]


# ---------------------------------------------------------------------------
# ANSI color support
# ---------------------------------------------------------------------------


_ANSI_RESET = "\x1b[0m"
_ANSI_BLUE = "\x1b[34m"
_ANSI_GREEN = "\x1b[32m"
_ANSI_YELLOW = "\x1b[33m"


def _display_width(s: str) -> int:
    """Return the terminal-cell width of ``s``.

    Treats East Asian Wide/Fullwidth characters (including emoji like 💭, 🔄,
    🌿) as 2 cells and skips control chars. ``len()`` counts code points, so
    it under-reports the width of emoji headers and produces ragged boxes.
    """
    return sum(
        2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        for ch in s
        if not unicodedata.category(ch).startswith("C")
    )


def _pad_cells(s: str, width: int) -> str:
    """Right-pad ``s`` with spaces so it occupies ``width`` terminal cells."""
    return s + " " * max(0, width - _display_width(s))


def _detect_color() -> bool:
    """Decide whether stderr should receive ANSI color codes.

    Honors the no-color.org convention (``NO_COLOR`` presence disables) and
    the de-facto ``FORCE_COLOR`` opt-in, falling back to TTY detection.
    """
    if "NO_COLOR" in os.environ:
        return False
    force = os.environ.get("FORCE_COLOR", "")
    if force and force != "0":
        return True
    return sys.stderr.isatty()


# ---------------------------------------------------------------------------
# Core server class
# ---------------------------------------------------------------------------


class SequentialThinkingServer:
    """In-memory store for an evolving chain of thoughts.

    The server keeps two structures:

    * ``thought_history`` – an append-only list of every thought processed.
    * ``branches`` – a mapping of branch identifier to the list of thoughts
      recorded under that branch (only populated when both
      ``branchFromThought`` and ``branchId`` are supplied).

    Whether thoughts are logged to stderr is controlled by the
    ``DISABLE_THOUGHT_LOGGING`` environment variable, which is read once when
    the instance is constructed (mirroring the behavior of the TypeScript
    reference implementation).
    """

    def __init__(
        self,
        *,
        use_color: bool | None = None,
        max_content_width: int | None = None,
    ) -> None:
        self.thought_history: list[dict[str, Any]] = []
        self.branches: dict[str, list[dict[str, Any]]] = {}
        self.disable_thought_logging: bool = (
            os.environ.get("DISABLE_THOUGHT_LOGGING", "").strip().lower() == "true"
        )
        self._use_color: bool = _detect_color() if use_color is None else use_color
        self._max_content_width: int | None = max_content_width

    def _resolve_max_content_width(self) -> int:
        if self._max_content_width is not None:
            return self._max_content_width
        terminal_width = shutil.get_terminal_size((80, 20)).columns
        return max(20, min(terminal_width - 4, 100))

    def _format_thought(self, thought_data: dict[str, Any]) -> str:
        """Render a thought as a Unicode box for stderr logging.

        Handles multi-line thoughts and word-wraps each segment to the
        terminal width (capped to 100 cols, floored at 20). When
        ``self._use_color`` is True, each rendered line is wrapped in an
        ANSI color sequence keyed off the thought kind (blue/yellow/green
        for regular/revision/branch). Padding is computed on the uncolored
        strings so the box stays rectangular.
        """
        thought_number = thought_data["thoughtNumber"]
        total_thoughts = thought_data["totalThoughts"]
        thought = thought_data["thought"]
        is_revision = thought_data.get("isRevision")
        revises_thought = thought_data.get("revisesThought")
        branch_from_thought = thought_data.get("branchFromThought")
        branch_id = thought_data.get("branchId")

        if is_revision:
            prefix = "🔄 Revision"
            context = f" (revising thought {revises_thought})"
            color = _ANSI_YELLOW
        elif branch_from_thought:
            prefix = "🌿 Branch"
            context = f" (from thought {branch_from_thought}, ID: {branch_id})"
            color = _ANSI_GREEN
        else:
            prefix = "💭 Thought"
            context = ""
            color = _ANSI_BLUE

        header = f"{prefix} {thought_number}/{total_thoughts}{context}"

        max_content_width = self._resolve_max_content_width()

        if thought == "":
            wrapped_lines: list[str] = [""]
        else:
            wrapped_lines = []
            for line in thought.splitlines():
                segments = textwrap.wrap(
                    line,
                    width=max_content_width,
                    break_long_words=True,
                    break_on_hyphens=False,
                )
                if not segments:
                    segments = [""]
                wrapped_lines.extend(segments)

        line_widths = [_display_width(line) for line in wrapped_lines]
        content_width = min(
            max(_display_width(header), *line_widths), max_content_width
        )

        border = "─" * (content_width + 2)
        box_lines = [
            f"┌{border}┐",
            f"│ {_pad_cells(header, content_width)} │",
            f"├{border}┤",
        ]
        for line in wrapped_lines:
            box_lines.append(f"│ {_pad_cells(line, content_width)} │")
        box_lines.append(f"└{border}┘")

        if self._use_color:
            box_lines = [f"{color}{line}{_ANSI_RESET}" for line in box_lines]

        return "\n" + "\n".join(box_lines)

    def process_thought(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Record a thought and return a summary of the current state.

        ``input_data`` is expected to already contain validated keys matching
        the tool schema. If ``thoughtNumber`` exceeds ``totalThoughts`` the
        latter is bumped up so that the running estimate stays internally
        consistent. The returned dict mirrors the structured payload that the
        MCP tool layer surfaces to clients.
        """
        if input_data["thoughtNumber"] > input_data["totalThoughts"]:
            input_data["totalThoughts"] = input_data["thoughtNumber"]

        self.thought_history.append(input_data)

        branch_from = input_data.get("branchFromThought")
        branch_id = input_data.get("branchId")
        if branch_from and branch_id:
            self.branches.setdefault(branch_id, []).append(input_data)

        if not self.disable_thought_logging:
            print(self._format_thought(input_data), file=sys.stderr)

        return {
            "thoughtNumber": input_data["thoughtNumber"],
            "totalThoughts": input_data["totalThoughts"],
            "nextThoughtNeeded": input_data["nextThoughtNeeded"],
            "branches": list(self.branches.keys()),
            "thoughtHistoryLength": len(self.thought_history),
        }


# ---------------------------------------------------------------------------
# Module-level helper for tests / non-MCP callers
# ---------------------------------------------------------------------------


def _process_thought_sync(
    server: SequentialThinkingServer, input_data: dict[str, Any]
) -> dict[str, Any]:
    """Thin synchronous wrapper around ``process_thought``.

    Mirrors the ``_query_sync`` pattern used elsewhere in this repo so that
    tests can exercise the core logic without spinning up an MCP server.
    """
    return server.process_thought(input_data)


# ---------------------------------------------------------------------------
# MCP Server setup
# ---------------------------------------------------------------------------


_SEQUENTIAL_THINKING_DESCRIPTION = """A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
  * Regular analytical steps
  * Revisions of previous thoughts
  * Questions about previous decisions
  * Realizations about needing more analysis
  * Changes in approach
  * Hypothesis generation
  * Hypothesis verification
- nextThoughtNeeded: True if you need more thinking, even if at what seemed like the end
- thoughtNumber: Current number in sequence (can go beyond initial total if needed)
- totalThoughts: Current estimate of thoughts needed (can be adjusted up/down)
- isRevision: A boolean indicating if this thought revises previous thinking
- revisesThought: If is_revision is true, which thought number is being reconsidered
- branchFromThought: If branching, which thought number is the branching point
- branchId: Identifier for the current branch (if any)
- needsMoreThoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set nextThoughtNeeded to false when truly done and a satisfactory answer is reached"""


mcp = FastMCP("sequential-thinking-server")
_thinking_server = SequentialThinkingServer()


# Mirrors the ToolAnnotations set on the TypeScript reference server
# (sequentialthinking/index.ts). The title lives inside annotations rather
# than as a top-level Tool.title because mcp==1.9.4 exposes the title only
# through ToolAnnotations.title — both FastMCP.tool() and types.Tool lack a
# top-level title field on this SDK.
_SEQUENTIAL_THINKING_ANNOTATIONS = ToolAnnotations(
    title="Sequential Thinking",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


@mcp.tool(
    description=_SEQUENTIAL_THINKING_DESCRIPTION,
    annotations=_SEQUENTIAL_THINKING_ANNOTATIONS,
)
async def sequentialthinking(
    thought: Annotated[str, Field(description="Your current thinking step")],
    nextThoughtNeeded: Annotated[  # noqa: N803
        CoercedBool,
        Field(description="Whether another thought step is needed"),
    ],
    thoughtNumber: Annotated[  # noqa: N803
        CoercedInt,
        Field(
            ge=1,
            description="Current thought number (numeric value, e.g., 1, 2, 3)",
        ),
    ],
    totalThoughts: Annotated[  # noqa: N803
        CoercedInt,
        Field(
            ge=1,
            description="Estimated total thoughts needed (numeric value, e.g., 5, 10)",
        ),
    ],
    isRevision: Annotated[  # noqa: N803
        OptionalCoercedBool,
        Field(default=None, description="Whether this revises previous thinking"),
    ] = None,
    revisesThought: Annotated[  # noqa: N803
        OptionalCoercedInt,
        Field(default=None, ge=1, description="Which thought is being reconsidered"),
    ] = None,
    branchFromThought: Annotated[  # noqa: N803
        OptionalCoercedInt,
        Field(default=None, ge=1, description="Branching point thought number"),
    ] = None,
    branchId: Annotated[  # noqa: N803
        str | None,
        Field(default=None, description="Branch identifier"),
    ] = None,
    needsMoreThoughts: Annotated[  # noqa: N803
        OptionalCoercedBool,
        Field(default=None, description="If more thoughts are needed"),
    ] = None,
) -> dict[str, Any]:
    """Record one step in a sequential thinking session."""
    input_data: dict[str, Any] = {
        "thought": thought,
        "thoughtNumber": thoughtNumber,
        "totalThoughts": totalThoughts,
        "nextThoughtNeeded": nextThoughtNeeded,
    }
    if isRevision is not None:
        input_data["isRevision"] = isRevision
    if revisesThought is not None:
        input_data["revisesThought"] = revisesThought
    if branchFromThought is not None:
        input_data["branchFromThought"] = branchFromThought
    if branchId is not None:
        input_data["branchId"] = branchId
    if needsMoreThoughts is not None:
        input_data["needsMoreThoughts"] = needsMoreThoughts

    # The TS reference server returns ``{"error": ..., "status": "failed"}``
    # alongside an ``isError=true`` content flag on uncaught exceptions. On
    # the pinned mcp==1.9.4 SDK we cannot set ``isError=true`` from a
    # FastMCP-decorated tool without raising, and raising would re-wrap the
    # body as ``"Error executing tool sequentialthinking: <msg>"`` — which
    # breaks clients that ``json.loads`` the content text. Catching here
    # preserves the TS body shape; the ``isError`` bit is a known divergence
    # that closes when we upgrade past 1.9.4.
    try:
        return _thinking_server.process_thought(input_data)
    except Exception as exc:
        return {"error": str(exc), "status": "failed"}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the FastMCP server over stdio."""
    parser = argparse.ArgumentParser(description="Sequential Thinking MCP Server")
    parser.parse_known_args()
    logger.info("Sequential Thinking MCP Server starting on stdio")
    mcp.run()


if __name__ == "__main__":
    main()
