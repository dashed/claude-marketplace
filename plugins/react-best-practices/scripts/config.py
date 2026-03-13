"""Configuration for the build tooling."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Base paths
PLUGIN_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent


@dataclass
class SkillConfig:
    name: str
    title: str
    description: str
    skill_dir: Path
    rules_dir: Path
    metadata_file: Path
    output_file: Path
    section_map: dict[str, int] = field(default_factory=dict)


SKILLS: dict[str, SkillConfig] = {
    "react-best-practices": SkillConfig(
        name="react-best-practices",
        title="React Best Practices",
        description="React and Next.js codebases",
        skill_dir=PLUGIN_DIR,
        rules_dir=PLUGIN_DIR / "rules",
        metadata_file=PLUGIN_DIR / "metadata.json",
        output_file=PLUGIN_DIR / "AGENTS.md",
        section_map={
            "async": 1,
            "bundle": 2,
            "server": 3,
            "client": 4,
            "rerender": 5,
            "rendering": 6,
            "js": 7,
            "advanced": 8,
        },
    ),
}

DEFAULT_SKILL = "react-best-practices"

# Legacy exports for backwards compatibility
RULES_DIR = SKILLS[DEFAULT_SKILL].rules_dir
METADATA_FILE = SKILLS[DEFAULT_SKILL].metadata_file
OUTPUT_FILE = SKILLS[DEFAULT_SKILL].output_file

# Test cases are build artifacts, not part of the skill
TEST_CASES_FILE = SCRIPTS_DIR / "test-cases.json"
