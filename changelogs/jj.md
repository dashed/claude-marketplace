# Changelog - jj

All notable changes to the jj skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.2.0] - 2026-05-23

### Added
- New commands: `jj arrange`, `jj bookmark advance`, `jj file search`, `jj util snapshot`
- New revset functions: `divergent()`, `remote_tags()`, `diff_lines()`, `diff_lines_added()`, `diff_lines_removed()`
- `xyz/n` versioned access syntax for hidden/divergent changes
- `--no-integrate-operation` global flag documentation
- `jj rebase --simplify-parents` flag
- `jj git push --option` for push options
- `jj bookmark rename --overwrite-existing` flag
- Pattern alias support (`name:x` syntax) in revsets
- Configuration: `remotes.<name>.fetch-bookmarks/fetch-tags`, `working-copy.exec-bit-change`, `--when.environments`, `JJ_PAGER`, `revsets.bookmark-advance-from/to`, `revsets.op-diff-changes-in`

### Changed
- Update skill to cover jj 0.37.0 through 0.41.0 (from 0.36.0)
- Update `jj bookmark track/untrack` to use `--remote` flag (old `@remote` syntax deprecated)
- Update push flag table: `--all`/`--tracked`/`-r` now skip ineligible bookmarks instead of failing
- Note `jj op undo` removed (use `jj op revert` or `jj undo`/`jj redo`)
- Note `diff_contains()` renamed to `diff_lines()`
- Note `git_head()` and `git_refs()` deprecated
- Note per-repo config moved outside repo (0.38)
- Note removed configs: `ui.always-allow-large-revsets`, `all:` modifier, `git.push-bookmark-prefix`, `ui.default-description`, `ui.diff.format`, `ui.diff.tool`, `core.fsmonitor`, `core.watchman.register-snapshot-trigger`
- Note minimum git version now 2.41.0
- Condensed Colocated Mode Deep Dive for brevity (progressive disclosure)
- Condensed binary/merge conflict resolution sections

## [1.1.0] - 2026-01-15

### Added
- Editor Settings section in references/configuration.md (for interactive/human use):
  - Priority order: `$JJ_EDITOR` > `ui.editor` > `$VISUAL` > `$EDITOR`
  - Terminal editor examples (vim, nvim, nano, emacs, micro, helix)
  - GUI editor configurations with wait flags (VS Code, Sublime, BBEdit, TextMate, IntelliJ)
  - Quick config commands (`jj config set --user ui.editor`)
  - Comparison table of `ui.editor` vs `ui.diff-editor` vs `ui.merge-editor`

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

### Changed
- SKILL.md Configuration section now emphasizes non-interactive workflows for LLM/automation use
- Removed editor setup from main SKILL.md (moved to references for human users)

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
