"""Parser for rule markdown files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .types import CodeExample, Rule

# Default section map (for backwards compatibility)
DEFAULT_SECTION_MAP: dict[str, int] = {
    "async": 1,
    "bundle": 2,
    "server": 3,
    "client": 4,
    "rerender": 5,
    "rendering": 6,
    "js": 7,
    "advanced": 8,
}


@dataclass
class RuleFile:
    section: int
    subsection: int | None
    rule: Rule


def parse_rule_file(
    file_path: str | Path,
    section_map: dict[str, int] | None = None,
) -> RuleFile:
    """Parse a rule markdown file into a Rule object."""
    file_path = Path(file_path)
    raw_content = file_path.read_text(encoding="utf-8")
    # Normalize Windows CRLF line endings to LF for consistent parsing
    content = raw_content.replace("\r\n", "\n")

    # Extract frontmatter if present
    frontmatter: dict[str, str] = {}
    content_start = 0

    if content.startswith("---"):
        frontmatter_end = content.index("---", 3) if "---" in content[3:] else -1
        if frontmatter_end != -1:
            # Adjust: content.index("---", 3) searches from position 3
            # but returns absolute position
            frontmatter_end = content.index("---", 3)
            frontmatter_text = content[3:frontmatter_end].strip()
            for line in frontmatter_text.split("\n"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    # Remove surrounding quotes
                    value = re.sub(r'^["\']|["\']$', "", value)
                    frontmatter[key] = value
            content_start = frontmatter_end + 3

    # Parse the rule content
    rule_content = content[content_start:].strip()
    rule_lines = rule_content.split("\n")

    # Extract title (first ## heading)
    title = ""
    title_line = 0
    for i, line in enumerate(rule_lines):
        if line.startswith("##"):
            title = re.sub(r"^##+\s*", "", line).strip()
            title_line = i
            break

    # Extract impact
    impact: str = "MEDIUM"
    impact_description = ""
    explanation = ""
    examples: list[CodeExample] = []
    references: list[str] = []

    # Parse content after title
    current_example: CodeExample | None = None
    in_code_block = False
    code_block_language = "typescript"
    code_block_content: list[str] = []
    after_code_block = False
    additional_text: list[str] = []
    has_code_block_for_current_example = False

    for i in range(title_line + 1, len(rule_lines)):
        line = rule_lines[i]

        # Impact line
        if "**Impact:" in line:
            pattern = r"\*\*Impact:\s*(\w+(?:-\w+)?)\s*(?:\(([^)]+)\))?"
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                impact = match.group(1).upper()
                impact_description = match.group(2) or ""
            continue

        # Code block start/end
        if line.startswith("```"):
            if in_code_block:
                # End of code block
                if current_example is not None:
                    current_example.code = "\n".join(code_block_content)
                    current_example.language = code_block_language
                code_block_content = []
                in_code_block = False
                after_code_block = True
            else:
                # Start of code block
                in_code_block = True
                has_code_block_for_current_example = True
                code_block_language = line[3:].strip() or "typescript"
                code_block_content = []
                after_code_block = False
            continue

        if in_code_block:
            code_block_content.append(line)
            continue

        # Example label (Incorrect, Correct, Example, Usage, Implementation, etc.)
        # Match pattern: **Label:** or **Label (description):** at end of line
        # This distinguishes example labels from inline bold text like "**Trade-off:** some text"
        label_match = re.match(r"^\*\*([^:]+?):\*?\*?$", line)
        if label_match:
            # Save previous example if it exists
            if current_example is not None:
                if additional_text:
                    current_example.additional_text = "\n\n".join(additional_text)
                    additional_text = []
                examples.append(current_example)
            after_code_block = False
            has_code_block_for_current_example = False

            full_label = label_match.group(1).strip()
            # Try to extract description from parentheses if present (handles simple cases)
            # For nested parentheses like "Incorrect (O(n) per lookup)", we keep the full label
            desc_match = re.match(r"^([A-Za-z]+(?:\s+[A-Za-z]+)*)\s*\(([^()]+)\)$", full_label)
            if desc_match:
                current_example = CodeExample(
                    label=desc_match.group(1).strip(),
                    description=desc_match.group(2).strip(),
                    code="",
                    language=code_block_language,
                )
            else:
                current_example = CodeExample(
                    label=full_label,
                    code="",
                    language=code_block_language,
                )
            continue

        # Reference links
        if line.startswith("Reference:") or line.startswith("References:"):
            # Save current example before processing references
            if current_example is not None:
                if additional_text:
                    current_example.additional_text = "\n\n".join(additional_text)
                    additional_text = []
                examples.append(current_example)
                current_example = None

            ref_matches = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", line)
            for _text, url in ref_matches:
                references.append(url)
            continue

        # Regular text (explanation or additional context after examples)
        if line.strip() and not line.startswith("#"):
            if current_example is None and not in_code_block:
                # Main explanation before any examples
                explanation += ("\n\n" if explanation else "") + line
            elif current_example is not None and (
                after_code_block or not has_code_block_for_current_example
            ):
                # Text after a code block, or text in a section without a code block
                additional_text.append(line)

    # Handle last example if still open
    if current_example is not None:
        if additional_text:
            current_example.additional_text = "\n\n".join(additional_text)
        examples.append(current_example)

    # Infer section from filename patterns
    # Pattern: area-description.md where area determines section
    filename = file_path.name

    effective_section_map = section_map if section_map is not None else DEFAULT_SECTION_MAP

    # Extract area from filename - try longest prefix match first
    # This handles prefixes like "list-performance" vs "list"
    filename_parts = filename.replace(".md", "").split("-")
    section = 0

    # Try progressively shorter prefixes to find the best match
    for length in range(len(filename_parts), 0, -1):
        prefix = "-".join(filename_parts[:length])
        if prefix in effective_section_map:
            section = effective_section_map[prefix]
            break

    # Fall back to frontmatter section if specified
    if "section" in frontmatter:
        section = int(frontmatter["section"])
    elif section == 0:
        section = 0

    # Build the Rule
    fm_references: list[str] = []
    if "references" in frontmatter:
        fm_references = [r.strip() for r in frontmatter["references"].split(",")]

    fm_tags: list[str] | None = None
    if "tags" in frontmatter:
        fm_tags = [t.strip() for t in frontmatter["tags"].split(",")]

    rule = Rule(
        id="",  # Will be assigned by build script based on sorted order
        title=frontmatter.get("title", title),
        section=section,
        subsection=None,
        impact=frontmatter.get("impact", impact),
        impact_description=frontmatter.get("impactDescription", impact_description),
        explanation=frontmatter.get("explanation", explanation.strip()),
        examples=examples,
        references=fm_references if fm_references else references,
        tags=fm_tags,
    )

    return RuleFile(
        section=section,
        subsection=0,
        rule=rule,
    )
