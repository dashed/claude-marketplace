# Changelog - skill-creator

All notable changes to the skill-creator skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-03-04

### Changed
- Complete SKILL.md rewrite with eval system, benchmarking, and description optimization workflows
- Replace references/output-patterns.md and references/workflows.md with references/schemas.md
- Update scripts/package_skill.py with enhanced packaging logic
- Update scripts/quick_validate.py with compatibility field validation

### Added
- agents/ directory with grader.md, comparator.md, and analyzer.md for evaluation
- eval-viewer/ directory with generate_review.py and viewer.html for reviewing eval results
- assets/eval_review.html for description eval review interface
- scripts/run_eval.py for running skill evaluations
- scripts/improve_description.py for automated description optimization
- scripts/aggregate_benchmark.py for statistical benchmarking
- scripts/run_loop.py for full optimization loops
- scripts/generate_report.py for HTML report generation
- scripts/utils.py with shared utilities
- scripts/__init__.py for package support

### Removed
- scripts/init_skill.py (skill initialization script)
- references/output-patterns.md
- references/workflows.md

## [1.0.0] - 2025-11-22

### Added
- Initial addition to marketplace from [Anthropic's skills repository](https://github.com/anthropics/skills/tree/main/skill-creator)
- Tool for creating and managing Agent Skills
- Version metadata (v1.0.0)
- Author information (Anthropic)
- License information (Apache-2.0)
- Keywords: skills, development, creation, tooling
- Plugin configuration with skills loading from root
