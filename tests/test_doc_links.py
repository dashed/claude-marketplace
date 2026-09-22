"""Local link checks must expose missing targets, anchor regressions, and gaps."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins/doc-quality/skills/doc-quality/scripts/doc_links.py"
)
_SPEC = importlib.util.spec_from_file_location("doc_links", _SCRIPT)
assert _SPEC and _SPEC.loader
links = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(links)


def check(text: str, root: Path, **kwargs: Any) -> dict[str, Any]:
    return links.check_links(text, root / "README.md", root, **kwargs)


def reasons(report: dict[str, Any]) -> list[str]:
    return [row["reason"] for row in report["links"]]


def test_missing_file_and_missing_anchor_are_distinct(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Exists\n")
    result = check("[ok](guide.md#exists) [bad](guide.md#gone) [missing](none.md)", tmp_path)
    assert result["status"] == "failed"
    assert result["counts"] == {"total": 3, "checked": 3, "broken": 2, "not_checked": 0}
    assert reasons(result) == ["anchor_exists", "missing_anchor", "missing_local_file"]


def test_deleted_heading_cannot_pass_against_stale_document_on_disk(tmp_path: Path) -> None:
    original = "# Removed\n\n[here](#removed) [self](README.md#removed)\n"
    revised = "# Renamed\n\n[here](#removed) [self](README.md#removed)\n"
    (tmp_path / "README.md").write_text(original)
    assert check(original, tmp_path)["status"] == "checked"
    result = check(revised, tmp_path)
    assert result["counts"]["broken"] == 2
    assert reasons(result) == ["missing_anchor", "missing_anchor"]


def test_unsaved_snapshot_has_a_logical_location_without_source_file(tmp_path: Path) -> None:
    source = "# Unsaved\n\n[one](#unsaved) [two](README.md#unsaved)\n"
    result = check(source, tmp_path)
    assert result["status"] == "checked"
    assert not (tmp_path / "README.md").exists()
    assert all(row["target"] == str(tmp_path / "README.md") for row in result["links"])


def test_slug_collision_sequence_uses_all_prior_heading_ids(tmp_path: Path) -> None:
    source = "# Foo\n# Foo-1\n# Foo\n# Foo-1\n\n"
    source += " ".join(f"[go](#{anchor})" for anchor in ("foo", "foo-1", "foo-2", "foo-1-1"))
    assert check(source, tmp_path)["status"] == "checked"
    assert reasons(check(source + " [bad](#foo-3)", tmp_path))[-1] == "missing_anchor"


def test_unicode_formatting_code_entities_and_punctuation_heading_ids(tmp_path: Path) -> None:
    source = (
        "# Héllo, *World*! `x_y` &amp; ~~gone~~\n"
        "# Привет 你好\n"
        "# 😄 emoji\n\n"
        "[a](#héllo-world-x_y--gone) [b](#привет-你好) [c](#-emoji)\n"
    )
    result = check(source, tmp_path)
    assert result["status"] == "checked", result
    assert result["renderer"]["github_slugger"] == "0.0.3"


def test_setext_and_nested_headings_are_real_but_fenced_headings_are_not(tmp_path: Path) -> None:
    source = (
        "Setext\n======\n\n> # Quoted\n\n- item\n\n  ## Nested\n\n"
        "```md\n# Fake\n<a id='fake-anchor'></a>\n[bad](missing.md)\n```\n\n"
        "    # Also fake\n\n[a](#setext) [b](#quoted) [c](#nested) [d](#fake)\n"
    )
    result = check(source, tmp_path)
    assert reasons(result) == ["anchor_exists"] * 3 + ["missing_anchor"]


def test_literal_html_anchors_do_not_consume_heading_duplicate_numbers(tmp_path: Path) -> None:
    source = (
        '<a name="same"></a>\n\n# Same\n# Same\n\n'
        '<span id="Exact-ID">anchor</span>\n\n'
        "[one](#same) [two](#same-1) [html](#Exact-ID) [wrong-case](#exact-id)\n"
    )
    result = check(source, tmp_path)
    assert reasons(result) == ["anchor_exists"] * 3 + ["missing_anchor"]


def test_html_targets_use_explicit_ids_without_generating_heading_ids(tmp_path: Path) -> None:
    (tmp_path / "page.html").write_text('<h1>Title</h1><div id="part"></div><a name="old"></a>')
    result = check("[a](page.html#part) [b](page.html#old) [c](page.html#title)", tmp_path)
    assert reasons(result) == ["anchor_exists", "anchor_exists", "missing_anchor"]


def test_raw_html_heading_in_markdown_is_conservative_about_renderer_behavior(
    tmp_path: Path,
) -> None:
    result = check("<h1>Title</h1>\n\n[go](#title)\n", tmp_path)
    assert result["status"] == "partial"
    assert reasons(result) == ["raw_html_heading_renderer_unknown"]


def test_reference_images_html_and_autolinks_have_original_usage_lines(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Part\n")
    (tmp_path / "image.png").write_bytes(b"image")
    source = (
        "---\ntitle: metadata\n---\n"
        "Intro [guide][ref]\n![pic][image]\n"
        '<https://example.invalid/>\n<a href="guide.md#part">HTML</a>\n'
        '<img src="image.png">\n\n'
        '[ref]: guide.md#part "Reference"\n[image]: image.png\n[unused]: missing.md\n'
    )
    result = check(source, tmp_path)
    assert [row["source_line"] for row in result["links"]] == [4, 5, 6, 7, 8]
    assert [row["kind"] for row in result["links"]] == [
        "link",
        "image",
        "link",
        "html_link",
        "html_image",
    ]
    assert reasons(result) == [
        "anchor_exists",
        "local_target_exists",
        "external_url",
        "anchor_exists",
        "local_target_exists",
    ]
    assert all(row["origin"] == str(tmp_path / "README.md") for row in result["links"])


def test_multiline_reference_usage_reports_opening_bracket_line(tmp_path: Path) -> None:
    (tmp_path / "ok.md").write_text("# Fine")
    source = "Intro\r\ncontinued [multi\r\nline][ref]\r\n\r\n[ref]: ok.md\r\n"
    assert check(source, tmp_path)["links"][0]["source_line"] == 2


def test_linked_image_does_not_parse_links_in_alt_text_as_links(tmp_path: Path) -> None:
    (tmp_path / "image.png").write_bytes(b"image")
    (tmp_path / "guide.md").write_text("# Guide")
    result = check("[![nested [fake](missing.md)](image.png)](guide.md)", tmp_path)
    assert [row["destination"] for row in result["links"]] == ["guide.md", "image.png"]
    assert result["status"] == "checked"


def test_percent_decoding_query_fragment_and_escaped_path_are_separate(tmp_path: Path) -> None:
    (tmp_path / "a #b.md").write_text("# Héllo World\n")
    (tmp_path / "file(1).md").write_text("# Fine\n")
    source = r"[one](a%20%23b.md?raw=true#h%C3%A9llo-world) [two](file\(1\).md#fine)"
    result = check(source, tmp_path)
    assert result["status"] == "checked", result
    assert result["links"][0]["target"] == str(tmp_path / "a #b.md")
    assert result["links"][0]["fragment"] == "héllo-world"


def test_percent_decoding_happens_once(tmp_path: Path) -> None:
    (tmp_path / "a%20b.md").write_text("# Fine")
    result = check("[one](a%2520b.md#fine)", tmp_path)
    assert result["status"] == "checked"
    assert result["links"][0]["target"] == str(tmp_path / "a%20b.md")


def test_leading_slash_is_root_relative_and_parent_links_respect_root(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "root.md").write_text("# Root\n")
    source = "[absolute](/root.md#root) [relative](../root.md#root)"
    result = links.check_links(source, tmp_path / "docs" / "README.md", tmp_path)
    assert result["status"] == "checked"


def test_empty_destination_empty_fragment_and_query_only_point_to_document(tmp_path: Path) -> None:
    result = check("[a]() [b](#) [c](?view=raw) [d](README.md#)", tmp_path)
    assert result["status"] == "checked"
    assert result["counts"]["checked"] == 4


@pytest.mark.parametrize(
    "destination,reason",
    [
        ("https://example.invalid/none", "external_url"),
        ("//example.invalid/none", "external_url"),
        ("mailto:user@example.invalid", "external_url"),
        ("file:///etc/passwd", "unsupported_scheme"),
        ("javascript:alert(1)", "unsupported_scheme"),
        ("data:text/plain,hello", "unsupported_scheme"),
        ("bad%FF.md", "invalid_percent_encoding"),
        ("bad%00.md", "unsupported_control_character"),
        ("bad%5Cname.md", "unsupported_backslash_path"),
    ],
)
def test_unsupported_destinations_are_never_opened(
    tmp_path: Path, monkeypatch: Any, destination: str, reason: str
) -> None:
    monkeypatch.setattr(links._TargetReader, "_open", lambda *unused: pytest.fail("target opened"))
    result = check(f"[go](<{destination}>)", tmp_path)
    assert result["status"] == "partial"
    assert reasons(result) == [reason]
    assert result["counts"] == {"total": 1, "checked": 0, "broken": 0, "not_checked": 1}


def test_autolink_with_file_scheme_is_explicitly_unsupported(tmp_path: Path) -> None:
    result = check("<file:///etc/passwd>", tmp_path)
    assert reasons(result) == ["unsupported_scheme"]


def test_outside_root_traversal_and_symlink_targets_are_not_opened(
    tmp_path: Path, monkeypatch: Any
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("# Secret\n")
    (root / "escape.md").symlink_to(outside)
    (root / "escape-dir").symlink_to(tmp_path, target_is_directory=True)
    monkeypatch.setattr(links._TargetReader, "_open", lambda *unused: pytest.fail("target opened"))
    source = "[a](../outside.md) [b](escape.md#secret) [c](escape-dir/outside.md#secret)"
    result = check(source, root)
    assert reasons(result) == ["outside_root"] * 3
    assert result["status"] == "partial"


def test_in_root_symlink_is_checked_and_self_alias_uses_snapshot(tmp_path: Path) -> None:
    (tmp_path / "target.md").write_text("# Target\n")
    (tmp_path / "alias.md").symlink_to(tmp_path / "target.md")
    (tmp_path / "README.md").write_text("# Stale\n")
    (tmp_path / "self.md").symlink_to(tmp_path / "README.md")
    result = check("# Fresh\n\n[a](alias.md#target) [b](self.md#fresh)", tmp_path)
    assert result["status"] == "checked"


def test_missing_or_file_root_is_partial(tmp_path: Path) -> None:
    file_root = tmp_path / "file"
    file_root.write_text("not a directory")
    for root in (tmp_path / "absent", file_root):
        result = links.check_links("[go](missing.md)", tmp_path / "README.md", root)
        assert result["status"] == "partial"
        assert reasons(result) == ["invalid_root_or_document_path"]


def test_anchor_checks_disabled_does_not_claim_fragment_success(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Present")
    result = check("[one](guide.md#missing) [two](guide.md)", tmp_path, anchors=False)
    assert result["status"] == "partial"
    assert reasons(result) == ["anchor_check_disabled", "local_target_exists"]


def test_non_markdown_fragment_and_directory_are_not_guessed(tmp_path: Path) -> None:
    (tmp_path / "image.svg").write_text('<svg id="part"></svg>')
    (tmp_path / "directory").mkdir()
    result = check("[a](image.svg#part) [b](directory)", tmp_path)
    assert result["status"] == "partial"
    assert reasons(result) == ["unsupported_anchor_target", "unsupported_target_type"]


def test_fragment_directive_is_not_a_missing_heading(tmp_path: Path) -> None:
    result = check("[text](#:~:text=example)", tmp_path)
    assert reasons(result) == ["unsupported_fragment_directive"]


def test_target_limit_does_not_hide_successful_file_existence(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(links, "MAX_TARGET_BYTES", 16)
    (tmp_path / "large.md").write_text("# Heading\n" + "x" * 100)
    result = check("[a](large.md#heading) [b](large.md)", tmp_path)
    assert reasons(result) == ["target_byte_limit", "local_target_exists"]
    assert result["status"] == "partial"


def test_byte_and_file_budgets_stop_target_reads(tmp_path: Path, monkeypatch: Any) -> None:
    for name in ("one", "two", "three"):
        (tmp_path / f"{name}.md").write_text("# Heading\n")
    monkeypatch.setattr(links, "MAX_TOTAL_TARGET_BYTES", 10)
    monkeypatch.setattr(links, "MAX_TARGET_FILES", 2)
    result = check("[a](one.md#heading) [b](two.md#heading) [c](three.md#heading)", tmp_path)
    assert reasons(result) == ["anchor_exists", "total_target_byte_limit", "target_file_limit"]


def test_repeated_target_is_read_once(tmp_path: Path, monkeypatch: Any) -> None:
    (tmp_path / "guide.md").write_text("# One\n# Two\n")
    original = links._TargetReader._open
    opened = []

    def capture(reader: Any, target: Path) -> int:
        opened.append(target)
        return original(reader, target)

    monkeypatch.setattr(links._TargetReader, "_open", capture)
    result = check("[a](guide.md#one) [b](guide.md#two) [c](guide.md#gone)", tmp_path)
    assert reasons(result) == ["anchor_exists", "anchor_exists", "missing_anchor"]
    assert len(opened) == 1


def test_source_and_inventory_limits_are_explicit(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setattr(links, "MAX_SOURCE_BYTES", 10)
    result = check("x" * 11, tmp_path)
    assert result["status"] == "partial"
    assert result["issues"] == [{"reason": "source_byte_limit"}]
    monkeypatch.setattr(links, "MAX_SOURCE_BYTES", 1000)
    monkeypatch.setattr(links, "MAX_LINKS", 1)
    result = check("[a](#) [b](#)", tmp_path)
    assert result["status"] == "partial"
    assert result["issues"] == [{"reason": "link_count_limit", "omitted_links": 1}]


def test_invalid_utf8_does_not_fabricate_a_missing_anchor(tmp_path: Path) -> None:
    (tmp_path / "binary.md").write_bytes(b"\xff\xfe")
    result = check("[a](binary.md#x) [b](binary.md)", tmp_path)
    assert reasons(result) == ["target_not_utf8", "local_target_exists"]


def test_fifo_is_not_read_or_blocked(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "pipe.md")
    assert reasons(check("[a](pipe.md#x)", tmp_path)) == ["unsupported_target_type"]


def test_link_targets_are_not_recursively_followed_or_executed(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text(
        "# Fine\n\n[missing](not-here.md)\n\n<script>throw Error('do not execute')</script>\n"
    )
    result = check("[a](guide.md#fine)", tmp_path)
    assert result["status"] == "checked"
    assert result["counts"]["total"] == 1


@pytest.mark.parametrize(
    "source", ["", "No links.", "`[code](missing.md)`", "[unused]: missing.md"]
)
def test_no_rendered_links_is_not_applicable(tmp_path: Path, source: str) -> None:
    result = check(source, tmp_path)
    assert result["status"] == "not_applicable"
    assert result["counts"] == {"total": 0, "checked": 0, "broken": 0, "not_checked": 0}


def test_inline_script_and_style_contents_do_not_create_html_anchors(tmp_path: Path) -> None:
    source = (
        'Before <script><a id="fake"></a></script> after.\n\n'
        'Before <style><a id="fake-style"></a></style> after.\n\n'
        "[one](#fake) [two](#fake-style)\n"
    )
    assert reasons(check(source, tmp_path)) == ["missing_anchor", "missing_anchor"]


def test_document_symlink_preserves_logical_directory_for_relative_links(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "source").mkdir()
    (tmp_path / "source" / "actual.md").write_text("# Stale\n")
    logical = tmp_path / "docs" / "README.md"
    logical.symlink_to(tmp_path / "source" / "actual.md")
    (tmp_path / "docs" / "neighbor.md").write_text("# Neighbor\n")
    result = links.check_links(
        "# Fresh\n\n[a](neighbor.md#neighbor) [b](README.md#fresh)", logical, tmp_path
    )
    assert result["status"] == "checked"


@pytest.mark.parametrize("fragment", ["top", "TOP", "ToP"])
def test_browser_top_fallback_after_explicit_anchors(tmp_path: Path, fragment: str) -> None:
    assert reasons(check(f"# Page\n\n[back](#{fragment})", tmp_path)) == ["document_top"]
    assert reasons(check(f'<a id="{fragment}"></a>\n\n[back](#{fragment})', tmp_path)) == [
        "anchor_exists"
    ]
