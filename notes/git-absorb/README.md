# Notes - git-absorb

Meta-documentation for the git-absorb skill plugin.

## Overview

The git-absorb skill enables automatic folding of uncommitted changes into appropriate commits on a feature branch. It simplifies the workflow of applying review feedback and maintaining atomic commit history without manual interactive rebasing.

## Contents

- [Analysis](./analysis.md) - Technical architecture, design patterns, and implementation deep-dive

## Key Insights

- **Automatic fixup generation**: Analyzes git diff and commit history to create fixup commits
- **Stack-based approach**: Works on commit stacks (feature branches)
- **Configuration flexibility**: Multiple options to control behavior
- **Progressive disclosure**: Uses references/ directory for detailed documentation

## Related Documentation

- [Plugin Source](../../plugins/git-absorb/)
- [Changelog](../../changelogs/git-absorb.md)
- [SKILL.md](../../plugins/git-absorb/SKILL.md)
- [Advanced Usage](../../plugins/git-absorb/references/advanced-usage.md)
- [Configuration](../../plugins/git-absorb/references/configuration.md)

## Version

Documented for git-absorb skill v1.0.0

## Future Documentation

Potential additions:
- `design-decisions.md` - Why progressive disclosure pattern, why references/ structure
- `testing-strategy.md` - How to test git-absorb integration
- `known-issues.md` - Edge cases, limitations, workarounds
