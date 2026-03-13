"""Tests for scripts.parser — parse_rule_file()."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from scripts.parser import parse_rule_file

# --- Frontmatter extraction ---


def test_frontmatter_title(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.title == "Promise.all() for Independent Operations"


def test_frontmatter_impact(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.impact == "CRITICAL"


def test_frontmatter_impact_description(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.impact_description == "2-10x improvement"


def test_frontmatter_tags(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.tags == ["async", "parallelization", "promises"]


# --- No frontmatter ---


def test_no_frontmatter_title(tmp_path: Path, sample_rule_no_frontmatter: str) -> None:
    f = tmp_path / "rerender-memo.md"
    f.write_text(sample_rule_no_frontmatter, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.title == "Use Memo for Expensive Calculations"


def test_no_frontmatter_impact_from_body(tmp_path: Path, sample_rule_no_frontmatter: str) -> None:
    f = tmp_path / "rerender-memo.md"
    f.write_text(sample_rule_no_frontmatter, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.impact == "HIGH"


def test_no_frontmatter_impact_description_from_body(
    tmp_path: Path, sample_rule_no_frontmatter: str
) -> None:
    f = tmp_path / "rerender-memo.md"
    f.write_text(sample_rule_no_frontmatter, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.impact_description == "significant CPU savings"


def test_no_frontmatter_tags_are_none(tmp_path: Path, sample_rule_no_frontmatter: str) -> None:
    f = tmp_path / "rerender-memo.md"
    f.write_text(sample_rule_no_frontmatter, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.tags is None


# --- Section inference from filename ---


def test_section_from_filename_async(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 1


def test_section_from_filename_bundle(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "bundle-splitting.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 2


def test_section_from_filename_server(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "server-caching.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 3


def test_section_from_filename_client(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "client-fetch.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 4


def test_section_from_filename_rerender(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "rerender-memo.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 5


def test_section_from_filename_rendering(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "rendering-virtualize.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 6


def test_section_from_filename_js(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "js-immutable.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 7


def test_section_from_filename_advanced(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "advanced-workers.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 8


def test_section_unknown_prefix_defaults_to_zero(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "unknown-thing.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 0


def test_section_custom_section_map(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "perf-thing.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f, section_map={"perf": 99})
    assert result.section == 99


def test_section_from_frontmatter_overrides_filename(tmp_path: Path) -> None:
    content = dedent("""\
        ---
        title: Override Section
        impact: MEDIUM
        section: 42
        ---

        ## Override Section

        Explanation.

        **Incorrect:**

        ```typescript
        bad()
        ```

        **Correct:**

        ```typescript
        good()
        ```
    """)
    f = tmp_path / "async-test.md"
    f.write_text(content, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.section == 42


# --- Code block parsing ---


def test_code_block_language_typescript(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    for example in result.rule.examples:
        assert example.language == "typescript"


def test_code_block_language_tsx(tmp_path: Path, sample_rule_tsx: str) -> None:
    f = tmp_path / "rendering-keys.md"
    f.write_text(sample_rule_tsx, encoding="utf-8")
    result = parse_rule_file(f)
    for example in result.rule.examples:
        assert example.language == "tsx"


def test_code_block_content(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    bad_example = result.rule.examples[0]
    assert "await fetchUser()" in bad_example.code
    good_example = result.rule.examples[1]
    assert "Promise.all" in good_example.code


def test_default_language_when_not_specified(tmp_path: Path) -> None:
    content = dedent("""\
        ## Test Rule

        Explanation.

        **Incorrect:**

        ```
        bad()
        ```

        **Correct:**

        ```
        good()
        ```
    """)
    f = tmp_path / "js-test.md"
    f.write_text(content, encoding="utf-8")
    result = parse_rule_file(f)
    for example in result.rule.examples:
        assert example.language == "typescript"


# --- Example label parsing ---


def test_example_labels_incorrect_correct(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert len(result.rule.examples) == 2
    assert result.rule.examples[0].label == "Incorrect"
    assert result.rule.examples[1].label == "Correct"


def test_example_description_parsing(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.examples[0].description == "sequential execution, 3 round trips"
    assert result.rule.examples[1].description == "parallel execution, 1 round trip"


def test_example_label_without_description(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "js-test.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.examples[0].label == "Incorrect"
    assert result.rule.examples[0].description is None
    assert result.rule.examples[1].label == "Correct"
    assert result.rule.examples[1].description is None


# --- Reference link extraction ---


def test_reference_links(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.references == ["https://react.dev"]


def test_no_references(tmp_path: Path, sample_rule_minimal: str) -> None:
    f = tmp_path / "js-test.md"
    f.write_text(sample_rule_minimal, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.references == []


def test_frontmatter_references_override_inline(tmp_path: Path) -> None:
    content = dedent("""\
        ---
        title: Test
        impact: MEDIUM
        references: https://example.com, https://example.org
        ---

        ## Test

        Explanation.

        **Incorrect:**

        ```typescript
        bad()
        ```

        **Correct:**

        ```typescript
        good()
        ```

        Reference: [Inline](https://inline.com)
    """)
    f = tmp_path / "js-test.md"
    f.write_text(content, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.references == ["https://example.com", "https://example.org"]


# --- Additional text after code blocks ---


def test_additional_text_after_code_block(
    tmp_path: Path, sample_rule_multiple_code_blocks: str
) -> None:
    f = tmp_path / "async-nested.md"
    f.write_text(sample_rule_multiple_code_blocks, encoding="utf-8")
    result = parse_rule_file(f)
    expected_0 = "This creates a waterfall of sequential requests."
    assert result.rule.examples[0].additional_text == expected_0
    expected_1 = "This makes the dependency chain explicit."
    assert result.rule.examples[1].additional_text == expected_1


# --- Edge cases ---


def test_crlf_line_endings(tmp_path: Path) -> None:
    content = (
        "---\r\ntitle: CRLF Test\r\nimpact: LOW\r\n---\r\n\r\n"
        "## CRLF Test\r\n\r\nExplanation.\r\n\r\n"
        "**Incorrect:**\r\n\r\n```typescript\r\nbad()\r\n```\r\n\r\n"
        "**Correct:**\r\n\r\n```typescript\r\ngood()\r\n```\r\n"
    )
    f = tmp_path / "js-crlf.md"
    f.write_bytes(content.encode("utf-8"))
    result = parse_rule_file(f)
    assert result.rule.title == "CRLF Test"
    assert result.rule.impact == "LOW"
    assert len(result.rule.examples) == 2


def test_missing_frontmatter_fields(tmp_path: Path) -> None:
    content = dedent("""\
        ---
        title: Only Title
        ---

        ## Only Title

        Explanation here.

        **Incorrect:**

        ```typescript
        bad()
        ```

        **Correct:**

        ```typescript
        good()
        ```
    """)
    f = tmp_path / "js-test.md"
    f.write_text(content, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.title == "Only Title"
    assert result.rule.impact == "MEDIUM"  # default
    assert result.rule.impact_description == ""
    assert result.rule.tags is None


def test_explanation_text(tmp_path: Path, sample_rule_md: str) -> None:
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert "no interdependencies" in result.rule.explanation


def test_rule_id_initially_empty(tmp_path: Path, sample_rule_md: str) -> None:
    """Rule IDs are assigned by the build script, not the parser."""
    f = tmp_path / "async-parallel.md"
    f.write_text(sample_rule_md, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.id == ""


def test_quoted_frontmatter_values(tmp_path: Path) -> None:
    content = dedent("""\
        ---
        title: "Quoted Title"
        impact: 'HIGH'
        ---

        ## Quoted Title

        Explanation.

        **Incorrect:**

        ```typescript
        bad()
        ```

        **Correct:**

        ```typescript
        good()
        ```
    """)
    f = tmp_path / "js-test.md"
    f.write_text(content, encoding="utf-8")
    result = parse_rule_file(f)
    assert result.rule.title == "Quoted Title"
    assert result.rule.impact == "HIGH"
