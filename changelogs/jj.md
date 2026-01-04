# Changelog - jj

All notable changes to the jj skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Working copy snapshot trigger explanation (when snapshots occur, how to force them)
- Binary file conflict resolution using `jj restore --from`
- Multi-parent (merge) conflict resolution workflow
- Colocated Mode Deep Dive section covering:
  - Git status interpretation ("HEAD detached from X" meaning)
  - Git index synchronization issues after jj conflict resolution
  - When git and jj disagree (import/export commands)
- Bookmark gotchas subsection:
  - `--allow-backwards` flag for moving bookmarks to ancestors
  - `*` suffix meaning (diverged from remote)
  - Create vs Set bookmark behavior
- Non-Interactive Workflows section covering:
  - Commit messages without editor (`-m` flag for describe, commit, new, squash, split)
  - Squash without editor (`-u` or `-m` flags)
  - Conflict resolution without merge tool (`--tool :ours/:theirs` or `jj restore`)
  - Inherently interactive commands and workarounds
- Common Pitfalls section covering:
  - Push flag combinations that don't work together
  - Working copy changes on merge commits
  - Git status in colocated mode
  - Bookmark movement refused scenarios
- Advanced Revset Recipes in revsets.md:
  - `roots(X ~ Y)` pattern for rebasing entire branch trees
  - Branch divergence analysis
  - Working with multiple feature branches
  - Finding merge commits
  - Complex rebase scenarios
- Push flag compatibility table in commands.md
- `--allow-new` flag documentation for `jj git push`
- Updated bookmark set command with `--allow-backwards` flag

## [1.0.0] - 2025-11-24

### Added
- Initial addition to marketplace
- Comprehensive SKILL.md covering:
  - Key concepts (working copy as commit, change IDs, no staging, first-class conflicts)
  - Essential commands quick reference table
  - Common workflows (new changes, editing, rebasing, bookmarks, pushing, conflicts)
  - Basic revsets reference
  - Git interoperability
  - Configuration basics
  - Troubleshooting guide
- Reference documentation in references/:
  - `revsets.md` - Complete revset language reference with all operators, functions, and patterns
  - `commands.md` - Full command reference organized by category with all options
  - `git-comparison.md` - Git to jj command mapping and workflow comparisons
  - `configuration.md` - Configuration reference including templates, filesets, aliases
- Skill triggers for "jj", "jujutsu", change IDs, operation log, revsets
