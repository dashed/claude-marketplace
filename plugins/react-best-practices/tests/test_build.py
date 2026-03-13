"""Tests for scripts.build — generate_markdown(), build_skill(), etc."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from scripts.build import generate_markdown, increment_version
from scripts.config import SkillConfig
from scripts.parser import parse_rule_file
from scripts.types import CodeExample, Rule, Section

# --- increment_version ---


def test_increment_version_patch() -> None:
    assert increment_version("1.0.0") == "1.0.1"


def test_increment_version_higher_patch() -> None:
    assert increment_version("1.0.9") == "1.0.10"


def test_increment_version_two_parts() -> None:
    assert increment_version("1.0") == "1.1"


# --- generate_markdown ---


def _make_metadata() -> dict[str, object]:
    return {
        "version": "1.0.0",
        "organization": "Engineering",
        "date": "March 2026",
        "abstract": "Performance guide.",
        "references": [],
    }


def _make_skill_config(tmp_path: Path) -> SkillConfig:
    return SkillConfig(
        name="test-skill",
        title="Test Skill",
        description="test codebases",
        skill_dir=tmp_path,
        rules_dir=tmp_path / "rules",
        metadata_file=tmp_path / "metadata.json",
        output_file=tmp_path / "AGENTS.md",
    )


def test_generate_markdown_header(tmp_path: Path) -> None:
    sections: list[Section] = []
    md = generate_markdown(sections, _make_metadata(), _make_skill_config(tmp_path))
    assert md.startswith("# Test Skill\n")
    assert "**Version 1.0.0**" in md
    assert "Engineering" in md


def test_generate_markdown_abstract(tmp_path: Path) -> None:
    sections: list[Section] = []
    md = generate_markdown(sections, _make_metadata(), _make_skill_config(tmp_path))
    assert "Performance guide." in md


def test_generate_markdown_toc(tmp_path: Path) -> None:
    rule = Rule(
        id="1.1",
        title="Test Rule",
        section=1,
        impact="HIGH",
        explanation="Explain.",
        examples=[],
    )
    section = Section(number=1, title="Async", impact="CRITICAL", rules=[rule])
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "1. [Async](#1-async)" in md
    assert "1.1 [Test Rule](#11-test-rule)" in md


def test_generate_markdown_section_heading(tmp_path: Path) -> None:
    section = Section(number=2, title="Bundle Size", impact="HIGH", rules=[])
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "## 2. Bundle Size" in md
    assert "**Impact: HIGH**" in md


def test_generate_markdown_section_with_impact_description(tmp_path: Path) -> None:
    section = Section(
        number=1, title="Async", impact="CRITICAL", impact_description="biggest gains", rules=[]
    )
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "**Impact: CRITICAL (biggest gains)**" in md


def test_generate_markdown_section_introduction(tmp_path: Path) -> None:
    section = Section(
        number=1,
        title="Async",
        impact="CRITICAL",
        introduction="Waterfalls are the #1 killer.",
        rules=[],
    )
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "Waterfalls are the #1 killer." in md


def test_generate_markdown_rule_content(tmp_path: Path) -> None:
    example = CodeExample(
        label="Incorrect",
        description="bad pattern",
        code="bad()",
        language="typescript",
    )
    rule = Rule(
        id="1.1",
        title="Test Rule",
        section=1,
        impact="HIGH",
        explanation="Do this instead.",
        examples=[example],
    )
    section = Section(number=1, title="Async", impact="CRITICAL", rules=[rule])
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "### 1.1 Test Rule" in md
    assert "**Impact: HIGH**" in md
    assert "Do this instead." in md
    assert "**Incorrect: bad pattern**" in md
    assert "```typescript\nbad()\n```" in md


def test_generate_markdown_example_without_description(tmp_path: Path) -> None:
    example = CodeExample(label="Correct", code="good()", language="typescript")
    rule = Rule(
        id="1.1",
        title="Test",
        section=1,
        impact="MEDIUM",
        explanation="X.",
        examples=[example],
    )
    section = Section(number=1, title="S", impact="MEDIUM", rules=[rule])
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "**Correct:**" in md


def test_generate_markdown_example_additional_text(tmp_path: Path) -> None:
    example = CodeExample(
        label="Correct",
        code="good()",
        language="typescript",
        additional_text="This is better because...",
    )
    rule = Rule(
        id="1.1",
        title="Test",
        section=1,
        impact="MEDIUM",
        explanation="X.",
        examples=[example],
    )
    section = Section(number=1, title="S", impact="MEDIUM", rules=[rule])
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "This is better because..." in md


def test_generate_markdown_empty_code_skips_block(tmp_path: Path) -> None:
    example = CodeExample(label="Note", code="", language="typescript")
    rule = Rule(
        id="1.1",
        title="Test",
        section=1,
        impact="MEDIUM",
        explanation="X.",
        examples=[example],
    )
    section = Section(number=1, title="S", impact="MEDIUM", rules=[rule])
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    # Should not contain a code fence for the empty example
    assert "```typescript\n\n```" not in md


def test_generate_markdown_references_in_rule(tmp_path: Path) -> None:
    rule = Rule(
        id="1.1",
        title="Test",
        section=1,
        impact="MEDIUM",
        explanation="X.",
        examples=[],
        references=["https://example.com"],
    )
    section = Section(number=1, title="S", impact="MEDIUM", rules=[rule])
    md = generate_markdown([section], _make_metadata(), _make_skill_config(tmp_path))
    assert "Reference: [https://example.com](https://example.com)" in md


def test_generate_markdown_global_references(tmp_path: Path) -> None:
    metadata = _make_metadata()
    metadata["references"] = ["https://react.dev", "https://nextjs.org"]
    md = generate_markdown([], metadata, _make_skill_config(tmp_path))
    assert "## References" in md
    assert "1. [https://react.dev](https://react.dev)" in md
    assert "2. [https://nextjs.org](https://nextjs.org)" in md


def test_generate_markdown_no_global_references_when_empty(tmp_path: Path) -> None:
    metadata = _make_metadata()
    metadata["references"] = []
    md = generate_markdown([], metadata, _make_skill_config(tmp_path))
    assert "## References" not in md


# --- Section grouping and rule sorting ---


def test_rules_grouped_by_section(tmp_path: Path) -> None:
    """Rules from different sections appear under their respective section headings."""
    rule1 = Rule(id="1.1", title="A Rule", section=1, impact="HIGH", explanation="X.", examples=[])
    rule2 = Rule(id="2.1", title="B Rule", section=2, impact="HIGH", explanation="Y.", examples=[])
    s1 = Section(number=1, title="Async", impact="CRITICAL", rules=[rule1])
    s2 = Section(number=2, title="Bundle", impact="HIGH", rules=[rule2])
    md = generate_markdown([s1, s2], _make_metadata(), _make_skill_config(tmp_path))
    async_pos = md.index("## 1. Async")
    bundle_pos = md.index("## 2. Bundle")
    assert async_pos < bundle_pos


# --- Full build integration test ---


def test_full_build_with_temp_rules(tmp_path: Path) -> None:
    """End-to-end: parse rules from temp dir, group, sort, assign IDs, generate markdown."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rule_a = dedent("""\
        ---
        title: Zebra Rule
        impact: HIGH
        ---

        ## Zebra Rule

        Zebras are fast.

        **Incorrect:**

        ```typescript
        slow()
        ```

        **Correct:**

        ```typescript
        fast()
        ```
    """)
    rule_b = dedent("""\
        ---
        title: Alpha Rule
        impact: MEDIUM
        ---

        ## Alpha Rule

        Alpha goes first.

        **Incorrect:**

        ```typescript
        bad()
        ```

        **Correct:**

        ```typescript
        good()
        ```
    """)
    (rules_dir / "async-zebra.md").write_text(rule_a, encoding="utf-8")
    (rules_dir / "async-alpha.md").write_text(rule_b, encoding="utf-8")

    # No _sections.md — uses defaults
    section_map = {"async": 1}

    # Parse both rules
    rf_a = parse_rule_file(rules_dir / "async-zebra.md", section_map)
    rf_b = parse_rule_file(rules_dir / "async-alpha.md", section_map)

    # Both should be in section 1
    assert rf_a.section == 1
    assert rf_b.section == 1

    # Group into section
    section = Section(number=1, title="Async", impact="CRITICAL", rules=[])
    section.rules.append(rf_a.rule)
    section.rules.append(rf_b.rule)

    # Sort by title (case-insensitive)
    section.rules.sort(key=lambda r: r.title.lower())

    # Assign IDs
    for idx, rule in enumerate(section.rules):
        rule.id = f"{section.number}.{idx + 1}"

    assert section.rules[0].title == "Alpha Rule"
    assert section.rules[0].id == "1.1"
    assert section.rules[1].title == "Zebra Rule"
    assert section.rules[1].id == "1.2"

    # Generate markdown
    metadata = _make_metadata()
    config = _make_skill_config(tmp_path)
    md = generate_markdown([section], metadata, config)

    # Verify ordering in output
    alpha_pos = md.index("### 1.1 Alpha Rule")
    zebra_pos = md.index("### 1.2 Zebra Rule")
    assert alpha_pos < zebra_pos


def test_sections_md_parsing(tmp_path: Path) -> None:
    """Test that _sections.md metadata is parsed correctly by build_skill."""
    import re

    sections_content = dedent("""\
        # Sections

        ---

        ## 1. Eliminating Waterfalls (async)

        **Impact:** CRITICAL
        **Description:** Waterfalls are the #1 killer.

        ## 2. Bundle Size Optimization (bundle)

        **Impact:** HIGH
        **Description:** Reduce bundle size.
    """)

    # Parse sections using the same logic as build_skill
    section_blocks = re.split(r"(?=^## \d+\. )", sections_content, flags=re.MULTILINE)
    section_blocks = [b for b in section_blocks if b.strip()]

    parsed_sections: dict[int, dict[str, str]] = {}
    for block in section_blocks:
        header_match = re.search(r"^## (\d+)\.\s+(.+?)(?:\s+\([^)]+\))?$", block, re.MULTILINE)
        if not header_match:
            continue
        num = int(header_match.group(1))
        title = header_match.group(2).strip()
        impact_match = re.search(r"\*\*Impact:\*\*\s+(\w+(?:-\w+)?)", block, re.IGNORECASE)
        impact = impact_match.group(1).upper() if impact_match else "MEDIUM"
        parsed_sections[num] = {"title": title, "impact": impact}

    assert parsed_sections[1]["title"] == "Eliminating Waterfalls"
    assert parsed_sections[1]["impact"] == "CRITICAL"
    assert parsed_sections[2]["title"] == "Bundle Size Optimization"
    assert parsed_sections[2]["impact"] == "HIGH"


def test_build_skill_integration(tmp_path: Path) -> None:
    """Integration test for build_skill with a real temp directory."""
    from scripts.build import build_skill

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rule_content = dedent("""\
        ---
        title: Test Integration Rule
        impact: HIGH
        ---

        ## Test Integration Rule

        Integration test explanation.

        **Incorrect:**

        ```typescript
        bad()
        ```

        **Correct:**

        ```typescript
        good()
        ```
    """)
    (rules_dir / "async-integration.md").write_text(rule_content, encoding="utf-8")

    metadata = {
        "version": "1.0.0",
        "organization": "Test",
        "date": "March 2026",
        "abstract": "Test abstract.",
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    output_path = tmp_path / "AGENTS.md"

    config = SkillConfig(
        name="test",
        title="Test Skill",
        description="test codebases",
        skill_dir=tmp_path,
        rules_dir=rules_dir,
        metadata_file=metadata_path,
        output_file=output_path,
        section_map={"async": 1},
    )

    build_skill(config)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# Test Skill" in content
    assert "Test Integration Rule" in content
    assert "1.1" in content


def test_build_skill_upgrade_version(tmp_path: Path) -> None:
    """Test that --upgrade-version increments the version."""
    from scripts.build import build_skill

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rule_content = dedent("""\
        ---
        title: Version Test
        impact: MEDIUM
        ---

        ## Version Test

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
    (rules_dir / "async-version.md").write_text(rule_content, encoding="utf-8")

    metadata = {"version": "1.0.0", "organization": "Test", "date": "2026", "abstract": "Test."}
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    config = SkillConfig(
        name="test",
        title="Test",
        description="test",
        skill_dir=tmp_path,
        rules_dir=rules_dir,
        metadata_file=metadata_path,
        output_file=tmp_path / "AGENTS.md",
        section_map={"async": 1},
    )

    build_skill(config, upgrade_version=True)

    updated = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert updated["version"] == "1.0.1"


def test_build_skill_missing_metadata_uses_defaults(tmp_path: Path) -> None:
    """When metadata.json doesn't exist, build_skill uses sensible defaults."""
    from scripts.build import build_skill

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rule_content = dedent("""\
        ---
        title: No Meta Rule
        impact: LOW
        ---

        ## No Meta Rule

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
    (rules_dir / "js-nometa.md").write_text(rule_content, encoding="utf-8")

    config = SkillConfig(
        name="test",
        title="Test",
        description="test",
        skill_dir=tmp_path,
        rules_dir=rules_dir,
        metadata_file=tmp_path / "nonexistent.json",
        output_file=tmp_path / "AGENTS.md",
        section_map={"js": 7},
    )

    build_skill(config)

    output = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "**Version 1.0.0**" in output
    assert "No Meta Rule" in output
