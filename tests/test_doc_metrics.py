"""Verify Markdown parsing boundaries and conservative revision guardrails."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins/doc-quality/skills/doc-quality/scripts/doc_metrics.py"
)
_SPEC = importlib.util.spec_from_file_location("doc_metrics", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
analyze_document = _MODULE.analyze_document
compare_documents = _MODULE.compare_documents


def test_real_headings_create_disjoint_sections_with_unique_line_ids() -> None:
    source = (
        "Preface.\n\n# Same\nFirst.\n\n```md\n# Fake\n```\n\n"
        "> # Quoted\n> quoted prose\n\n## Child\nSecond.\n\n"
        "Same\n====\nLast.\n"
    )
    result = analyze_document(source)
    sections = result["sections"]
    assert [row["title"] for row in sections] == ["", "Same", "Child", "Same"]
    assert [row["heading_path"] for row in sections] == [[], ["Same"], ["Same", "Child"], ["Same"]]
    assert len({row["id"] for row in sections}) == 4
    assert [row["id"] for row in sections] == ["section-1", "section-3", "section-13", "section-16"]
    assert "".join(row["text"] for row in sections) == source
    assert all(
        left["end_line"] + 1 == right["start_line"] for left, right in zip(sections, sections[1:])
    )
    assert sum(row["metrics"]["word_count"] for row in sections) == result["metrics"]["word_count"]
    assert result["metrics"]["heading_depths"] == [1, 2, 1]


def test_skipped_heading_levels_preserve_parent_path() -> None:
    sections = analyze_document("# A\n### B\n## C\n#### D\n# E\n")["sections"]
    assert [row["heading_path"] for row in sections] == [
        ["A"],
        ["A", "B"],
        ["A", "C"],
        ["A", "C", "D"],
        ["E"],
    ]


def test_nested_list_heading_does_not_create_document_section() -> None:
    source = "# Main\n\n- Item\n\n  ## Nested\n\n  Content.\n\n# Last\n"
    report = analyze_document(source)
    assert [section["title"] for section in report["sections"]] == ["Main", "Last"]
    assert report["metrics"]["heading_depths"] == [1, 1]


def test_code_is_protected_and_excluded_from_readability() -> None:
    source = "Plain words here.\n\n```python\nsecret_code_name 123 MUST NOT\n```\n\n    more_secret_code\n\nNext `inline_secret` words.\n"
    report = analyze_document(source)
    assert report["metrics"]["word_count"] == 5
    assert report["metrics"]["word_character_counts"] == [5, 5, 4, 4, 5]
    assert report["metrics"]["mean_characters_per_word"] == 4.6
    assert report["metrics"]["sentence_word_counts"] == [3, 2]
    assert report["metrics"]["paragraph_word_counts"] == [3, 2]
    assert report["protected"]["quantities"] == []
    assert report["protected"]["requirement_modals"] == []
    assert [row["kind"] for row in report["protected"]["code_blocks"]] == ["fence", "code_block"]
    assert report["protected"]["code_blocks"][0]["info"] == "python"
    assert report["protected"]["inline_code"] == [
        {"text": "inline_secret", "source": "`inline_secret`"}
    ]


def test_reference_links_images_and_unused_duplicate_definitions_are_retained() -> None:
    source = (
        "Read [guide][doc], ![map][pic], and [direct](/direct).\n\n"
        '[doc]: /guide "Guide"\n[pic]: image.png\n[unused]: /elsewhere\n[doc]: /duplicate\n'
    )
    protected = analyze_document(source)["protected"]
    assert [(row["kind"], row["destination"]) for row in protected["link_destinations"]] == [
        ("link", "/guide"),
        ("image", "image.png"),
        ("link", "/direct"),
    ]
    assert [row["destination"] for row in protected["reference_definitions"]] == [
        "/guide",
        "image.png",
        "/elsewhere",
        "/duplicate",
    ]
    assert protected["link_destinations"][0]["title"] == "Guide"


def test_frontmatter_and_raw_html_are_protected_without_becoming_prose() -> None:
    report = analyze_document(
        "---\ntitle: hidden metadata\n---\n# Visible\n\n<div>hidden html</div>\n\nReadable <b>words</b>.\n"
    )
    assert report["metrics"]["word_count"] == 3
    assert report["protected"]["frontmatter"][0]["format"] == "yaml"
    assert len(report["protected"]["raw_html"]) == 3
    assert [row["title"] for row in report["sections"]] == ["", "Visible"]
    assert report["sections"][1]["start_line"] == 4


def test_table_cells_and_list_paragraphs_contribute_visible_prose() -> None:
    source = "| Name | Value |\n| --- | --- |\n| alpha | beta |\n\n- List item.\n- Next item.\n"
    metrics = analyze_document(source)["metrics"]
    assert metrics["word_count"] == 8
    assert metrics["paragraph_word_counts"] == [2, 2]


@pytest.mark.parametrize("source", ["", "\n\n", "```python\npass\n```\n"])
def test_no_prose_does_not_fabricate_readability_scores(source: str) -> None:
    metrics = analyze_document(source)["metrics"]
    assert metrics["word_count"] == metrics["sentence_count"] == 0
    assert metrics["readability"]["flesch_reading_ease"] is None
    assert metrics["readability"]["flesch_kincaid_grade"] is None


def test_repeated_sentence_normalization_is_deterministic() -> None:
    text = "Keep the output quite simple.\n\nKEEP the output quite simple!\n"
    result = analyze_document(text)
    assert result == analyze_document(text)
    assert result["metrics"]["repeated_sentences"] == [
        {"text": "keep the output quite simple", "occurrences": 2}
    ]


@pytest.mark.parametrize(
    "original,revised,category",
    [
        ("```py\nprint(1)\n```", "```py\nprint(2)\n```", "code_blocks"),
        ("```py\nx\n```", "```sh\nx\n```", "code_blocks"),
        ("Use `x`.", "Use `y`.", "inline_code"),
        ("Use `` x ``.", "Use `x`.", "inline_code"),
        ("[go](/first)", "[go](/second)", "link_destinations"),
        ("![map](first.png)", "![map](second.png)", "link_destinations"),
        ("[x]: /first\n", "[x]: /second\n", "reference_definitions"),
        ("---\nkey: first\n---\n", "---\nkey: second\n---\n", "frontmatter"),
        ('<div id="a">x</div>', '<div id="b">x</div>', "raw_html"),
    ],
)
def test_protected_mutations_are_detected(original: str, revised: str, category: str) -> None:
    result = compare_documents(original, revised)
    check = result["hard_preservation"]["checks"][category]
    assert result["status"] == "needs_review"
    assert result["hard_preservation"]["status"] == "changed"
    assert check["added_count"] == check["removed_count"] == 1
    assert check["status"] == "changed"


def test_duplicate_removal_and_code_reordering_are_detected_separately() -> None:
    duplicate = compare_documents("`x` and `x`", "`x`")["hard_preservation"]["checks"][
        "inline_code"
    ]
    assert duplicate["removed_count"] == 1 and duplicate["added_count"] == 0
    reordered = compare_documents("```\na\n```\n\n```\nb\n```\n", "```\nb\n```\n\n```\na\n```\n")
    check = reordered["hard_preservation"]["checks"]["code_blocks"]
    assert check["sequence_changed"] and check["status"] == "changed"
    assert check["added_count"] == check["removed_count"] == 0


def test_equal_quantity_inventory_does_not_prove_binding_preservation() -> None:
    result = compare_documents("A gets 5 ms; B gets 10 ms.", "B gets 5 ms; A gets 10 ms.")
    assert result["semantic_review"]["checks"]["quantities"]["status"] == "unchanged"
    assert result["status"] == "needs_review"
    assert result["meaning_preservation"] == "not_established"
    assert result["semantic_review"]["required"]


def test_requirement_weakening_and_lost_negation_require_review() -> None:
    weakened = compare_documents("Clients MUST retry.", "Clients SHOULD retry.")
    assert (
        weakened["semantic_review"]["checks"]["requirement_modals"]["removed"][0]["value"] == "must"
    )
    dropped = compare_documents("Do not delete the backup.", "Do delete the backup.")
    assert dropped["semantic_review"]["checks"]["negations"]["removed_count"] == 1
    assert dropped["meaning_preservation"] == weakened["meaning_preservation"] == "not_established"
    assert dropped["status"] == weakened["status"] == "needs_review"


def test_identical_text_is_unchanged_without_claiming_semantic_proof() -> None:
    result = compare_documents("# Text\nA must use 5 ms.\n", "# Text\nA must use 5 ms.\n")
    assert result["status"] == "unchanged"
    assert result["hard_preservation"]["status"] == "unchanged"
    assert not result["semantic_review"]["required"]
    assert result["meaning_preservation"] == "not_established"


def test_crlf_source_ranges_preserve_input_bytes() -> None:
    source = "Intro\r\n\r\n# Heading\r\n```py\r\nx\r\n```\r\n"
    report = analyze_document(source)
    assert "".join(section["text"] for section in report["sections"]) == source
    assert report["protected"]["code_blocks"][0]["source"] == "```py\r\nx\r\n```\r\n"


def test_frontmatter_mask_keeps_multiline_reference_source_offsets() -> None:
    source = '+++\ntitle = "Meta"\n+++\n\n# Doc\n[guide][ref]\n\n[ref]:\n  /guide\n  "A title"\n'
    protected = analyze_document(source)["protected"]
    assert protected["frontmatter"][0]["format"] == "toml"
    assert protected["reference_definitions"][0]["source"] == '[ref]:\n  /guide\n  "A title"\n'
    assert protected["link_destinations"][0]["destination"] == "/guide"


@pytest.mark.parametrize(
    "revised,added,removed",
    [
        ("# Renamed\n## Child\n# Same\n", 1, 1),
        ("# Same\n## Child\n", 0, 1),
        ("# Same\n# Same\n## Child\n", 0, 0),
    ],
)
def test_heading_rename_removal_and_reordering_require_anchor_review(
    revised: str, added: int, removed: int
) -> None:
    original = "# Same\n## Child\n# Same\n"
    result = compare_documents(original, revised)
    headings = result["semantic_review"]["checks"]["headings"]
    assert headings["status"] == "changed" and headings["sequence_changed"]
    assert headings["added_count"] == added and headings["removed_count"] == removed
    assert result["hard_preservation"]["status"] == "unchanged"
    assert result["status"] == "needs_review"
    assert result["meaning_preservation"] == "not_established"
    assert any("renderer-specific link checks" in note for note in result["limitations"])


def test_heading_inventory_ignores_line_number_shifts() -> None:
    original = "# Main `code`\n\nText.\n\nChild\n-----\n"
    revised = "New preamble.\n\n" + original.replace("Text.\n", "Text.\n\nMore text.\n")
    headings = analyze_document(original)["protected"]["headings"]
    assert headings == [{"depth": 1, "title": "Main code"}, {"depth": 2, "title": "Child"}]
    result = compare_documents(original, revised)
    assert result["semantic_review"]["checks"]["headings"]["status"] == "unchanged"
    assert result["status"] == "needs_review"
