# Changelog - delete-comment

All notable changes to the delete-comment skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-11-20

### Added
- Initial addition to the marketplace: a four-phase comment purge for a codebase or directory. It inventories every comment, classifies each one as a tautology, stale, an excuse, or a decision record, acts on each (delete; file an issue, then delete; encode in a name, type, assertion, or test, or move into an ADR, then delete), and reports the measured lines removed.
- The policy table orders the tests (stale, excuse, decision record, tautology) and separates the two hard categories: an excuse says the code should change; a decision record says it must stay as it is.
- `scripts/comments.py` (PEP 723, depends only on pygments), with three commands:
  - `inventory` lexes each file with pygments, so a comment marker in a string or regex is not a comment. Each item gets a kind: `plain`, `doc`, `directive` (shebangs, encoding cookies, PEP 723 blocks, lint, type-check, format, coverage, and secret-scanner directives, build constraints, GHC pragmas, Makefile `##` help text), or `license`. Patterns that only mean something in one language family are scoped to it: Python type comments, switch fall-through comments, Rust `SAFETY:`, and Dockerfile and TOML directives. Consecutive full-line comments form one item. Hints (`todo`, `excuse`, `code`, `divider`) are leads for classification.
  - `estimate` reports comment-only lines per kind and per verdict category. It says plainly that code lines, and so SLOC, do not change.
  - `delete` applies a verdicts file. Excuses need an issue `ref` (a URL, `owner/repo#N`, `#N`, a tracker key such as `ENG-341`, or an existing file), so a placeholder such as "tbd" does not pass; decision records need a `ref` that is a URL or an existing path. Directive and license items are never deleted. Every file is lexed again before it is written and must keep the same code tokens; Python files must also keep the same AST.
  - `--exclude`, `--allow`, and `--language` narrow the scan, add a repository's own directives, and pick languages.
- `references/adr.md`: where ADRs live, a template for recovered decisions, how to find the commit behind a comment with `git log -S` and `-L`, writing rules, and three ways to keep ADRs findable once the code cannot point to them.
- Verification: on this repository the scanner's comment-only, trailing, and code line counts match Python's `tokenize` in all 84 Python files. Deleting every plain and doc comment (2,868 items, 4,357 lines, the estimated figure) left every Python, shell, JS, TS, TOML, and YAML file parseable, and all 216 tests passed on the stripped copy. On a 15,000-file TypeScript and Python application, a scan takes about 11 seconds; an audit of its 3,000 directive items there led to the language-scoped patterns and a stricter region-marker pattern, so prose such as "region URL." stays a plain comment.
- An agent given the original prompt and this skill on a four-file fixture classified all 11 plain comments as expected, kept the 4 functional ones, and carried both decision records into tests and ADRs. An agent without the skill deleted both tool directives and reported 13 removed lines as lines of code shed. The first agent's notes led to the stricter excuse refs and clearer wording for scan paths and repository-local skills.
- Built from a user-supplied comment-cleanup prompt. Changes from that prompt: tool directives, license notices, docstrings, and doc comments are kept, because deleting them changes tool behavior or published docs; a decision record goes into code or a test before an ADR; the line estimate is measured; the prompt's lint rule is left out; and the "create a /delete-comment skill in the repository" step is this skill, with the repository's settings recorded in `AGENTS.md` or `CLAUDE.md`.
