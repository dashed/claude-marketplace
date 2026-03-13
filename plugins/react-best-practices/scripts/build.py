"""Build script to compile individual rule files into AGENTS.md."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime

from .config import DEFAULT_SKILL, SKILLS, SkillConfig
from .parser import RuleFile, parse_rule_file
from .types import Section


def increment_version(version: str) -> str:
    """Increment a semver-style version string (e.g., '0.1.0' -> '0.1.1')."""
    parts = [int(p) for p in version.split(".")]
    parts[-1] += 1
    return ".".join(str(p) for p in parts)


def generate_markdown(
    sections: list[Section],
    metadata: dict[str, object],
    skill_config: SkillConfig,
) -> str:
    """Generate markdown from rules."""
    md = f"# {skill_config.title}\n\n"
    md += f"**Version {metadata['version']}**  \n"
    md += f"{metadata['organization']}  \n"
    md += f"{metadata['date']}\n\n"
    md += "> **Note:**  \n"
    md += "> This document is mainly for agents and LLMs to follow when maintaining,  \n"
    md += f"> generating, or refactoring {skill_config.description}. Humans  \n"
    md += "> may also find it useful, but guidance here is optimized for automation  \n"
    md += "> and consistency by AI-assisted workflows.\n\n"
    md += "---\n\n"
    md += "## Abstract\n\n"
    md += f"{metadata['abstract']}\n\n"
    md += "---\n\n"
    md += "## Table of Contents\n\n"

    # Generate TOC
    for section in sections:
        title_slug = re.sub(r"\s+", "-", section.title.lower())
        section_anchor = f"{section.number}-{title_slug}"
        md += (
            f"{section.number}. [{section.title}](#{section_anchor}) \u2014 **{section.impact}**\n"
        )
        for rule in section.rules:
            # GitHub generates anchors from the full heading text:
            # "1.1 Title" -> "#11-title"
            anchor = f"{rule.id} {rule.title}".lower()
            anchor = re.sub(r"\s+", "-", anchor)
            anchor = re.sub(r"[^\w-]", "", anchor)
            md += f"   - {rule.id} [{rule.title}](#{anchor})\n"

    md += "\n---\n\n"

    # Generate sections
    for section in sections:
        md += f"## {section.number}. {section.title}\n\n"
        impact_desc = f" ({section.impact_description})" if section.impact_description else ""
        md += f"**Impact: {section.impact}{impact_desc}**\n\n"
        if section.introduction:
            md += f"{section.introduction}\n\n"

        for rule in section.rules:
            md += f"### {rule.id} {rule.title}\n\n"
            rule_impact_desc = f" ({rule.impact_description})" if rule.impact_description else ""
            md += f"**Impact: {rule.impact}{rule_impact_desc}**\n\n"
            md += f"{rule.explanation}\n\n"

            for example in rule.examples:
                if example.description:
                    md += f"**{example.label}: {example.description}**\n\n"
                else:
                    md += f"**{example.label}:**\n\n"
                # Only generate code block if there's actual code
                if example.code and example.code.strip():
                    lang = example.language or "typescript"
                    md += f"```{lang}\n"
                    md += f"{example.code}\n"
                    md += "```\n\n"
                if example.additional_text:
                    md += f"{example.additional_text}\n\n"

            if rule.references:
                refs = ", ".join(f"[{ref}]({ref})" for ref in rule.references)
                md += f"Reference: {refs}\n\n"

        md += "---\n\n"

    # Add references section
    refs_list = metadata.get("references")
    if refs_list and isinstance(refs_list, list) and len(refs_list) > 0:
        md += "## References\n\n"
        for i, ref in enumerate(refs_list):
            md += f"{i + 1}. [{ref}]({ref})\n"

    return md


def build_skill(
    skill_config: SkillConfig,
    upgrade_version: bool = False,
) -> None:
    """Build a single skill."""
    print(f"\nBuilding {skill_config.name}...")
    print(f"  Rules directory: {skill_config.rules_dir}")
    print(f"  Output file: {skill_config.output_file}")

    # Read all rule files (exclude files starting with _ and README.md)
    rules_dir = skill_config.rules_dir
    files = sorted(
        f.name
        for f in rules_dir.iterdir()
        if f.suffix == ".md" and not f.name.startswith("_") and f.name != "README.md"
    )

    rule_data: list[RuleFile] = []
    for filename in files:
        file_path = rules_dir / filename
        try:
            parsed = parse_rule_file(file_path, skill_config.section_map)
            rule_data.append(parsed)
        except Exception as e:
            print(f"  Error parsing {filename}: {e}", file=sys.stderr)

    # Group rules by section
    sections_map: dict[int, Section] = {}

    for rf in rule_data:
        sec_num = rf.section
        if sec_num not in sections_map:
            sections_map[sec_num] = Section(
                number=sec_num,
                title=f"Section {sec_num}",
                impact=rf.rule.impact,
            )
        sections_map[sec_num].rules.append(rf.rule)

    # Sort rules within each section by title (case-insensitive for consistency)
    for section in sections_map.values():
        section.rules.sort(key=lambda r: r.title.lower())

        # Assign IDs based on sorted order
        for index, rule in enumerate(section.rules):
            rule.id = f"{section.number}.{index + 1}"
            rule.subsection = index + 1

    # Convert to array and sort
    sections = sorted(sections_map.values(), key=lambda s: s.number)

    # Read section metadata from consolidated _sections.md file
    sections_file = rules_dir / "_sections.md"
    try:
        sections_content = sections_file.read_text(encoding="utf-8")

        # Parse sections using regex to match each section block
        section_blocks = re.split(r"(?=^## \d+\. )", sections_content, flags=re.MULTILINE)
        section_blocks = [b for b in section_blocks if b.strip()]

        for block in section_blocks:
            # Extract section number and title, removing section ID in parentheses
            header_match = re.search(r"^## (\d+)\.\s+(.+?)(?:\s+\([^)]+\))?$", block, re.MULTILINE)
            if not header_match:
                continue

            section_number = int(header_match.group(1))
            section_title = header_match.group(2).strip()

            # Extract impact (format: **Impact:** CRITICAL)
            impact_match = re.search(r"\*\*Impact:\*\*\s+(\w+(?:-\w+)?)", block, re.IGNORECASE)
            impact_level = impact_match.group(1).upper() if impact_match else "MEDIUM"

            # Extract description (format: **Description:** text)
            desc_match = re.search(r"\*\*Description:\*\*\s+(.+?)(?=\n\n##|$)", block, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""

            # Update section if it exists
            for section in sections:
                if section.number == section_number:
                    section.title = section_title
                    section.impact = impact_level
                    section.introduction = description
                    break
    except FileNotFoundError:
        print("  Warning: Could not read _sections.md, using defaults")

    # Read metadata
    try:
        metadata_content = skill_config.metadata_file.read_text(encoding="utf-8")
        metadata = json.loads(metadata_content)
    except (FileNotFoundError, json.JSONDecodeError):
        now = datetime.now()
        metadata = {
            "version": "1.0.0",
            "organization": "Engineering",
            "date": now.strftime("%B %Y"),
            "abstract": (
                f"Performance optimization guide for {skill_config.description}, ordered by impact."
            ),
        }

    # Upgrade version if flag is passed
    if upgrade_version:
        old_version = metadata["version"]
        metadata["version"] = increment_version(old_version)
        print(f"  Upgrading version: {old_version} -> {metadata['version']}")

        # Write updated metadata.json
        skill_config.metadata_file.write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
        print("  Updated metadata.json")

        # Update SKILL.md frontmatter if it exists
        skill_file = skill_config.skill_dir / "SKILL.md"
        try:
            skill_content = skill_file.read_text(encoding="utf-8")
            updated = re.sub(
                r'^(---[\s\S]*?version:\s*)"[^"]*"([\s\S]*?---)$',
                rf'\g<1>"{metadata["version"]}"\g<2>',
                skill_content,
                flags=re.MULTILINE,
            )
            skill_file.write_text(updated, encoding="utf-8")
            print("  Updated SKILL.md")
        except FileNotFoundError:
            pass  # SKILL.md doesn't exist, skip

    # Generate markdown
    markdown = generate_markdown(sections, metadata, skill_config)

    # Write output
    skill_config.output_file.write_text(markdown, encoding="utf-8")

    print(f"  Built AGENTS.md with {len(sections)} sections and {len(rule_data)} rules")


def build(
    skill_name: str | None = None,
    build_all: bool = False,
    upgrade_version: bool = False,
) -> None:
    """Main build function."""
    try:
        print("Building AGENTS.md from rules...")

        if build_all:
            for skill in SKILLS.values():
                build_skill(skill, upgrade_version=upgrade_version)
        elif skill_name:
            skill = SKILLS.get(skill_name)
            if not skill:
                print(f"Unknown skill: {skill_name}", file=sys.stderr)
                print(f"Available skills: {', '.join(SKILLS.keys())}", file=sys.stderr)
                sys.exit(1)
            build_skill(skill, upgrade_version=upgrade_version)
        else:
            # Build default skill (backwards compatibility)
            build_skill(SKILLS[DEFAULT_SKILL], upgrade_version=upgrade_version)

        print("\nBuild complete")
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
