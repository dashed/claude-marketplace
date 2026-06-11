# Changelog - handoff

All notable changes to the handoff skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.3.0] - 2026-06-11

### Added
- `--tracked` option (also triggered by asking for a git-visible/committed/shared handoff): saves to the workspace root with the file visible to git — removes any leftover `handoff-*.md` line from `.git/info/exclude` (which would otherwise hide the file and make `git add` refuse without `-f`), stages the file, and offers (never auto-runs) commit + push since committing the handoff is the cross-machine transfer path; next-session starter becomes `git pull && claude "Read ./handoff-… and continue"`. `argument-hint` updated to `[--workspace | --tracked]`

## [1.2.0] - 2026-06-11

### Added
- Predictable filename (`handoff-<project>-<YYYY-MM-DD-HHMM>.md`, also in `--workspace` mode) and a closing path announcement with a ready-to-paste starter for the next session — a temp-dir doc with an unspecified name was effectively lost
- `references/handoff-template.md` (progressive disclosure): Header / Goal / Done / In progress / Next steps / Decisions & rationale / Dead ends tried / Verify state / Suggested skills / Open questions; sections scale to the work, but decisions-with-rationale and dead-ends-tried are always captured when present
- State anchors (timestamp, branch, commit SHA, dirty files) plus a "Verify state" section with exact baseline-verification commands and expected results, making staleness detectable
- Scope guidance: suggest `--resume`/`--continue` for same-machine resumable sessions; durable facts go to memory, the handoff carries task state only
- `--workspace` mode now adds `handoff-*.md` to `.git/info/exclude` (not `.gitignore`) so docs stay invisible to `git status`

### Changed
- These additions substantially extend the upstream skill — the body is no longer verbatim from mattpocock/skills (upstream's five core instructions are retained unchanged)

### Added
- `--workspace` option (also triggered by asking for the document in the workspace): saves the handoff doc to the workspace root as `HANDOFF.md` instead of the OS temp directory, left untracked and uncommitted unless asked; `argument-hint` updated to mention the flag. Second divergence from upstream, which is temp-dir only

## [1.0.0] - 2026-06-11

### Added
- Initial addition to marketplace — ported from [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md) (`skills/productivity/handoff`, MIT)
- Compacts the current conversation into a handoff document a fresh agent can pick up: saved to the OS temp directory (not the workspace), includes a "suggested skills" section, references existing artifacts (PRDs, plans, ADRs, issues, commits, diffs) by path/URL instead of duplicating them, redacts secrets/PII, and tailors the doc to the optional argument describing what the next session is for (`argument-hint` supported)

### Changed
- Marketplace adaptation (only divergence from upstream): extended the frontmatter `description` with house-convention "Use when..." triggers (session handoff, context transfer, approaching context limits, explicit "handoff" phrasing); skill body kept verbatim
