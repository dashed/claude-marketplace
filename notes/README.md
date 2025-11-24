# Plugin Notes

Meta-documentation for plugins in the marketplace.

## Purpose

This directory contains developer/maintainer documentation about plugins:
- **Technical analysis** - Architecture, design patterns, implementation details
- **Design decisions** - Rationale for choices made, trade-offs considered
- **Testing strategies** - Plugin-specific testing approaches
- **Known issues** - Current limitations, workarounds, edge cases
- **Implementation notes** - Key insights, gotchas, lessons learned

## Directory Structure

Each plugin has its own subdirectory with topic-based documentation:

```
notes/
├── README.md                    # This file
├── <plugin-name>/
│   ├── README.md                # Overview and index
│   ├── analysis.md              # Technical deep-dive
│   ├── design-decisions.md      # Rationale and trade-offs
│   ├── testing-strategy.md      # Testing approaches
│   └── ...                      # Other topic-specific docs
```

## Available Plugins

### [git-absorb](./git-absorb/)
Automatically fold uncommitted changes into appropriate commits on a feature branch.

### [skill-creator](./skill-creator/)
Tool for creating and managing Agent Skills.

### [skill-reviewer](./skill-reviewer/)
Review and ensure Agent Skills maintain high quality standards.

### [tmux](./tmux/)
Remote control tmux sessions for interactive CLIs (Python, gdb, etc.) by sending keystrokes and scraping pane output.

## Relationship to Other Documentation

- **[plugins/](../plugins/)** - Actual plugin code and runtime documentation
  - `SKILL.md` - For Claude to read when executing the skill
  - `references/` - For Claude to load as needed during execution

- **[changelogs/](../changelogs/)** - Historical record
  - What changed, when, and in which version
  - Marketplace perspective on plugin evolution

- **[notes/](./README.md)** - Conceptual understanding (this directory)
  - Why things are the way they are
  - How things work internally
  - Developer/maintainer perspective

- **[references/](../references/)** - General reference material
  - Not plugin-specific
  - Concepts, patterns, guides applicable to all plugins

## Contributing

When adding documentation for a new plugin:
1. Create subdirectory: `notes/<plugin-name>/`
2. Add `README.md` with overview
3. Create topic-specific files as needed
4. Update this index

## Format

All documentation is in Markdown format, following [CommonMark](https://commonmark.org/) specification.
