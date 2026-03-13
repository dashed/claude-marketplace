"""Type definitions for React Performance Guidelines rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ImpactLevel = Literal["CRITICAL", "HIGH", "MEDIUM-HIGH", "MEDIUM", "LOW-MEDIUM", "LOW"]

VALID_IMPACT_LEVELS: list[str] = ["CRITICAL", "HIGH", "MEDIUM-HIGH", "MEDIUM", "LOW-MEDIUM", "LOW"]


@dataclass
class CodeExample:
    label: str  # e.g., "Incorrect", "Correct", "Example"
    code: str = ""
    description: str | None = None  # Optional description before code
    language: str | None = None  # Default: 'typescript' or 'tsx'
    additional_text: str | None = None  # Optional text after code block


@dataclass
class Rule:
    id: str  # e.g., "1.1", "2.3"
    title: str
    section: int  # Main section number (1-8)
    impact: str  # ImpactLevel
    explanation: str = ""
    subsection: int | None = None  # Subsection number within section
    impact_description: str = ""  # e.g., "2-10x improvement"
    examples: list[CodeExample] = field(default_factory=list)
    references: list[str] = field(default_factory=list)  # URLs or citations
    tags: list[str] | None = None  # For categorization/search


@dataclass
class Section:
    number: int
    title: str
    impact: str  # ImpactLevel
    impact_description: str = ""
    introduction: str = ""
    rules: list[Rule] = field(default_factory=list)


@dataclass
class TestCase:
    rule_id: str
    rule_title: str
    type: Literal["bad", "good"]
    code: str
    language: str = "typescript"
    description: str = ""
