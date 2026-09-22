"""Bounded, read-only local link checks for a declared Markdown rendering profile.

Heading IDs use github-slugger rather than a home-grown punctuation regex. The
profile is CommonMark with tables/strikethrough, generated Markdown heading IDs,
and literal HTML IDs/named anchors; it is not a complete GitHub rendering service.
No network, document scripts, includes, or target link traversal are performed.
"""

from __future__ import annotations

import errno
import os
import re
import stat
from collections.abc import Callable
from html.parser import HTMLParser
from importlib.metadata import version
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from github_slugger import GithubSlugger
from markdown_it import MarkdownIt
from markdown_it.rules_inline import autolink, html_inline, image, link
from markdown_it.rules_inline.state_inline import StateInline
from markdown_it.token import Token

MAX_SOURCE_BYTES = 1_048_576
MAX_TARGET_BYTES = 1_048_576
MAX_TOTAL_TARGET_BYTES = 8_388_608
MAX_TARGET_FILES = 64
MAX_LINKS = 10_000
_MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mkd"}
_HTML_SUFFIXES = {".html", ".htm"}
_BAD_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
LIMITATIONS = [
    "Only parsed CommonMark links/images, used reference links, angle-bracket autolinks, "
    "and literal HTML a[href]/img[src] are inventoried; bare URLs and undefined or unused "
    "reference definitions are not rendered links in this profile.",
    "The anchor profile is CommonMark plus tables/strikethrough, github-slugger generated "
    "Markdown heading IDs, and literal HTML id/a[name] values. It does not reproduce all "
    "GitHub sanitization, extensions, emoji expansion, site routing, or other renderers.",
    "A closed YAML/TOML block at the document start is treated as frontmatter, not content.",
    "Relative links resolve from the logical document directory; leading slash links "
    "resolve from the explicit root. Query strings do not affect filesystem existence.",
    "External URLs and unsupported schemes are never fetched. Directory routes, includes, "
    "target document links, redirects, and non-Markdown/non-HTML fragments are not checked.",
    "Supplied text is authoritative for links back to the logical document, including "
    "unsaved or comparison snapshots. Other targets are the current files on disk.",
    "Checks use bounded local reads and are not an atomic snapshot of the filesystem.",
]


def _positioned(
    rule: Callable[[StateInline, bool], bool], kind: str
) -> Callable[[StateInline, bool], bool]:
    def capture(state: StateInline, silent: bool) -> bool:
        start, count = state.pos, len(state.tokens)
        matched = rule(state, silent)
        if matched and not silent:
            for token in state.tokens[count:]:
                if token.type == kind:
                    token.meta["line_offset"] = state.src.count("\n", 0, start)
                    break
        return matched

    return capture


class _InventoryParser(MarkdownIt):
    def validateLink(self, url: str) -> bool:
        # Inventory unsafe schemes too: tokens are inspected, never executed/rendered.
        return True


def _parse(text: str) -> list[Token]:
    # Mask frontmatter while preserving one-based source line coordinates.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").removeprefix("\ufeff")
    lines = normalized.splitlines(keepends=True)
    if lines and lines[0].rstrip("\n") in {"---", "+++"}:
        closers = {"---", "..."} if lines[0].rstrip("\n") == "---" else {"+++"}
        for index, line in enumerate(lines[1:], 1):
            if line.rstrip("\n") in closers:
                normalized = "\n" * (index + 1) + "".join(lines[index + 1 :])
                break
    parser = _InventoryParser("commonmark").enable(["table", "strikethrough"])
    for name, rule, kind in (
        ("link", link, "link_open"),
        ("image", image, "image"),
        ("autolink", autolink, "link_open"),
        ("html_inline", html_inline, "html_inline"),
    ):
        parser.inline.ruler.at(name, _positioned(rule, kind))
    return parser.parse(normalized)


class _HTMLInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: set[str] = set()
        self.links: list[dict[str, Any]] = []
        self.unidentified_heading = False
        self.source_offset = 0

    def feed_at(self, source: str, line: int) -> None:
        self.source_offset = line - self.getpos()[0]
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        anchor = values.get("id")
        if anchor:
            self.anchors.add(anchor)
        if tag == "a" and values.get("name"):
            self.anchors.add(str(values["name"]))
        if re.fullmatch(r"h[1-6]", tag) and not anchor:
            self.unidentified_heading = True
        attribute = "href" if tag == "a" else "src" if tag == "img" else None
        if attribute and values.get(attribute) is not None:
            self.links.append(
                {
                    "kind": "html_link" if tag == "a" else "html_image",
                    "destination": values[attribute],
                    "source_line": self.source_offset + self.getpos()[0],
                }
            )


def _html(source: str) -> _HTMLInventory:
    parsed = _HTMLInventory()
    parsed.feed(source)
    parsed.close()
    return parsed


def _heading_text(tokens: list[Token]) -> str:
    # Images have no DOM text content: their alt attributes are not heading text.
    return "".join(
        token.content
        if token.type in {"text", "code_inline"}
        else "\n"
        if token.type in {"softbreak", "hardbreak"}
        else ""
        for token in tokens
    ).strip()


def _markdown_inventory(text: str) -> tuple[list[dict[str, Any]], set[str], bool]:
    tokens = _parse(text)
    rows: list[dict[str, Any]] = []
    anchors: set[str] = set()
    raw = _HTMLInventory()
    slugger = GithubSlugger()
    for index, token in enumerate(tokens):
        line = token.map[0] + 1 if token.map else 1
        if token.type == "heading_open" and index + 1 < len(tokens):
            anchors.add(slugger.slug(_heading_text(tokens[index + 1].children or [])))
        children = token.children or [] if token.type == "inline" else [token]
        for child in children:
            child_line = line + child.meta.get("line_offset", 0)
            if child.type in {"link_open", "image"}:
                rows.append(
                    {
                        "kind": "image" if child.type == "image" else "link",
                        "destination": child.attrGet("src" if child.type == "image" else "href")
                        or "",
                        "source_line": child_line,
                    }
                )
            elif child.type in {"html_inline", "html_block"}:
                count = len(raw.links)
                # Preserve script/style state across inline raw HTML tokens.
                raw.feed_at(child.content, child_line)
                rows.extend(raw.links[count:])
    raw.close()
    anchors.update(raw.anchors)
    return rows, anchors, raw.unidentified_heading


class _TargetReader:
    """Open resolved paths beneath one root, rejecting symlink races and devices."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.total_bytes = 0
        self.targets: dict[Path, dict[str, Any]] = {}

    def close(self) -> None:
        os.close(self.root_fd)

    def _open(self, target: Path) -> int:
        parts = target.relative_to(self.root).parts
        if not parts:
            return os.dup(self.root_fd)
        directory = os.dup(self.root_fd)
        try:
            for part in parts[:-1]:
                next_directory = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
                )
                os.close(directory)
                directory = next_directory
            return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        finally:
            os.close(directory)

    def inspect(self, target: Path, need_anchors: bool) -> dict[str, Any]:
        existing = self.targets.get(target)
        if existing is not None and (
            not need_anchors or "anchors" in existing or existing["error"]
        ):
            if not need_anchors and existing.get("file_exists"):
                return {"error": None, "status": "checked"}
            return existing
        if existing is None and len(self.targets) >= MAX_TARGET_FILES:
            return {"error": "target_file_limit", "status": "not_checked"}
        result: dict[str, Any] = {"error": None, "status": "checked"}
        self.targets[target] = result
        descriptor = None
        try:
            descriptor = self._open(target)
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode):
                result.update(error="unsupported_target_type", status="not_checked")
            elif need_anchors:
                result["file_exists"] = True
                remaining = min(MAX_TARGET_BYTES, MAX_TOTAL_TARGET_BYTES - self.total_bytes)
                if info.st_size > remaining:
                    reason = (
                        "target_byte_limit"
                        if info.st_size > MAX_TARGET_BYTES
                        else "total_target_byte_limit"
                    )
                    result.update(error=reason, status="not_checked")
                else:
                    chunks = []
                    size = 0
                    while size <= remaining:
                        chunk = os.read(descriptor, min(65_536, remaining + 1 - size))
                        if not chunk:
                            break
                        chunks.append(chunk)
                        size += len(chunk)
                    self.total_bytes += size
                    if size > remaining:
                        result.update(error="target_byte_limit", status="not_checked")
                    else:
                        content = b"".join(chunks).decode("utf-8-sig")
                        if target.suffix.lower() in _HTML_SUFFIXES:
                            parsed = _html(content)
                            found, uncertain = parsed.anchors, False
                        else:
                            _, found, uncertain = _markdown_inventory(content)
                        result.update(anchors=found, uncertain_html=uncertain)
            else:
                result["file_exists"] = True
        except (FileNotFoundError, NotADirectoryError):
            result.update(error="missing_local_file", status="broken")
        except UnicodeError:
            result.update(error="target_not_utf8", status="not_checked")
        except OSError as exc:
            reason = (
                "target_changed_or_symlink" if exc.errno == errno.ELOOP else "target_unreadable"
            )
            result.update(error=reason, status="not_checked")
        finally:
            if descriptor is not None:
                os.close(descriptor)
        return result


def _finish(row: dict[str, Any], status: str, reason: str) -> dict[str, Any]:
    return {**row, "status": status, "reason": reason}


def _check(
    row: dict[str, Any],
    document: Path,
    resolved_document: Path,
    root: Path,
    reader: _TargetReader,
    own_anchors: set[str],
    uncertain_html: bool,
    check_anchors: bool,
) -> dict[str, Any]:
    destination = row["destination"]
    if _CONTROL.search(destination):
        return _finish(row, "not_checked", "unsupported_control_character")
    try:
        url = urlsplit(destination)
    except ValueError:
        return _finish(row, "not_checked", "invalid_url")
    if url.netloc or destination.startswith("//") or url.scheme in {"http", "https", "mailto"}:
        return _finish(row, "not_checked", "external_url")
    if url.scheme:
        return _finish(row, "not_checked", "unsupported_scheme")
    if _BAD_PERCENT.search(url.path) or _BAD_PERCENT.search(url.fragment):
        return _finish(row, "not_checked", "invalid_percent_encoding")
    try:
        path, fragment = unquote(url.path, errors="strict"), unquote(url.fragment, errors="strict")
    except UnicodeError:
        return _finish(row, "not_checked", "invalid_percent_encoding")
    if _CONTROL.search(path) or _CONTROL.search(fragment):
        return _finish(row, "not_checked", "unsupported_control_character")
    if "\\" in path:
        return _finish(row, "not_checked", "unsupported_backslash_path")
    try:
        target = (
            document
            if not path
            else root / path.lstrip("/")
            if path.startswith("/")
            else document.parent / path
        ).resolve()
    except (OSError, RuntimeError, ValueError):
        return _finish(row, "not_checked", "target_resolution_failed")
    row = {**row, "target": str(target), "fragment": fragment}
    if not target.is_relative_to(root):
        return _finish(row, "not_checked", "outside_root")
    same_document = target == resolved_document
    anchor_supported = same_document or target.suffix.lower() in _MARKDOWN_SUFFIXES | _HTML_SUFFIXES
    inspected: dict[str, Any]
    if same_document:
        inspected = {"error": None, "anchors": own_anchors, "uncertain_html": uncertain_html}
    else:
        inspected = reader.inspect(target, bool(fragment and check_anchors and anchor_supported))
    if inspected["error"]:
        return _finish(row, inspected["status"], inspected["error"])
    if not fragment:
        return _finish(row, "checked", "local_target_exists" if path else "document_top")
    if not check_anchors:
        return _finish(row, "not_checked", "anchor_check_disabled")
    if not anchor_supported:
        return _finish(row, "not_checked", "unsupported_anchor_target")
    if ":~:" in fragment:
        return _finish(row, "not_checked", "unsupported_fragment_directive")
    if fragment in inspected["anchors"]:
        return _finish(row, "checked", "anchor_exists")
    if fragment.lower() == "top":
        return _finish(row, "checked", "document_top")
    if inspected["uncertain_html"]:
        return _finish(row, "not_checked", "raw_html_heading_renderer_unknown")
    return _finish(row, "broken", "missing_anchor")


def check_links(
    text: str, document_path: Path, root: Path, *, anchors: bool = True
) -> dict[str, Any]:
    """Check local destinations; ``document_path`` is the text's logical location.

    ``root`` must be an existing directory and is the only permitted target read
    boundary. The logical document need not exist; same-document links always use
    ``text``. ``counts.checked`` includes broken links, with ``broken`` a subset.
    """
    issues: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    if len(text.encode("utf-8")) > MAX_SOURCE_BYTES:
        issues.append({"reason": "source_byte_limit"})
    else:
        parsed, own_anchors, uncertain_html = _markdown_inventory(text)
        if len(parsed) > MAX_LINKS:
            issues.append({"reason": "link_count_limit", "omitted_links": len(parsed) - MAX_LINKS})
        inventory = [
            {**row, "origin": str(document_path), "target": None, "fragment": None}
            for row in parsed[:MAX_LINKS]
        ]
        reader = None
        try:
            resolved_root = root.resolve(strict=True)
            if not resolved_root.is_dir():
                raise NotADirectoryError(str(root))
            document = document_path.absolute()
            resolved_document = document.resolve()
            reader = _TargetReader(resolved_root)
        except (OSError, RuntimeError, ValueError):
            issues.append({"reason": "invalid_root_or_document_path"})
            rows = [
                _finish(row, "not_checked", "invalid_root_or_document_path") for row in inventory
            ]
        else:
            try:
                rows = [
                    _check(
                        row,
                        document,
                        resolved_document,
                        resolved_root,
                        reader,
                        own_anchors,
                        uncertain_html,
                        anchors,
                    )
                    for row in inventory
                ]
            finally:
                reader.close()
    broken = sum(row["status"] == "broken" for row in rows)
    unchecked = sum(row["status"] == "not_checked" for row in rows)
    status = (
        "failed"
        if broken
        else "partial"
        if unchecked or issues
        else "checked"
        if rows
        else "not_applicable"
    )
    return {
        "status": status,
        "counts": {
            "total": len(rows),
            "checked": len(rows) - unchecked,
            "broken": broken,
            "not_checked": unchecked,
        },
        "links": rows,
        "issues": issues,
        "renderer": {
            "profile": "commonmark-github-slugger-with-literal-html-anchors",
            "markdown_it_py": version("markdown-it-py"),
            "github_slugger": version("github-slugger"),
            "anchor_checks_enabled": anchors,
        },
        "limits": {
            "source_bytes": MAX_SOURCE_BYTES,
            "target_bytes": MAX_TARGET_BYTES,
            "total_target_bytes": MAX_TOTAL_TARGET_BYTES,
            "target_files": MAX_TARGET_FILES,
            "links": MAX_LINKS,
        },
        "limitations": LIMITATIONS,
    }
