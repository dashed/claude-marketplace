---
name: delete-comment
description: "Purge comments from a codebase or directory and keep them from coming back. Inventory every code comment with a lexer, classify each as tautology, stale, excuse, or decision record, delete tautologies and stale comments, file an issue for each excuse before deleting it, move each decision record into an ADR or encode it as a name, assertion, or test, then add a lint rule that bans new comments with a per-file ratchet baseline, and measure the lines removed. Keeps tool directives, license notices, and doc comments; deletes only after a check that the code tokens did not change. Use when asked to delete, purge, ban, or audit every comment in a codebase, package, or directory; to sort comments into tautology, excuse, stale, and decision record; to move comment rationale into ADRs or file issues for hacks that comments excuse; to add a no-comments lint rule or comment ratchet; to estimate how many lines deleting comments saves; or for /delete-comment. For comments in one diff or PR, use comment-slop."
license: MIT
---

# Delete Comment

This skill removes the comments a codebase does not need and keeps the facts that some comments carry. It runs in five phases:

1. **Inventory** every comment with a lexer and measure the lines a purge would remove.
2. **Classify** each comment as a tautology, stale, an excuse, or a decision record.
3. **Act**: delete tautologies and stale comments, file an issue for each excuse, move each decision record into code, a test, or an ADR, then delete those comments too.
4. **Ratchet**: add a lint rule that bans new comments and records the remaining ones in a per-file baseline that can only go down.
5. **Report** the measured result.

The scanner, `scripts/comments.py`, does the mechanical work: it finds comments with a real lexer, keeps the comments that tools read, deletes only what the verdicts allow, and checks that no code token changed. You do the judgment: what each comment is, and where its fact goes.

## The policy

| Category | The comment… | Action |
|---|---|---|
| **Tautology** | says what the code already says: a name, a type, the next line, a section divider | Delete |
| **Stale** | is false now: it names code that moved, describes old behavior, or is commented-out code | Delete |
| **Excuse** | admits or excuses a defect: `TODO`, `FIXME`, `HACK`, "workaround", "for now", "not ideal", "legacy" | File an issue, then delete |
| **Decision record** | states a non-obvious decision or an outside fact that a change must respect | Encode it in code or a test if you can; otherwise write an ADR. Then delete |

Apply the tests in this order, and take the first that fits:

1. **Stale?** A false comment carries nothing worth keeping, even if it reads like a decision or an excuse. Check the claim against the code before you trust it.
2. **Excuse?** The comment says the code *should* change. The issue must exist before the comment goes, because the comment is the only record of the defect.
3. **Decision record?** The comment says the code *must not* change, although it looks wrong: a guard, an ordering, a retry count, a format an outside system requires. Its fact must land in code, a test, or an ADR before the comment goes.
4. **Otherwise it is a tautology.**

The test between the two hard categories: an excuse says *this should be different*; a decision record says *this must stay as it is*. "Sleep 2 s because the ready event is not wired up yet" is an excuse. "Sleep 2 s: the vendor rate-limits bursts and returns 429 without a Retry-After" is a decision record.

### What the scanner keeps without a verdict

Some comments are read by tools, so deleting them changes behavior. The scanner gives them the kind `directive` or `license` and never deletes them, and the lint rule allows them:

- shebangs, encoding cookies, editor modelines, PEP 723 `# /// script` blocks
- lint, type-check, format, and coverage directives: `noqa`, `type: ignore`, `pyright:`, `eslint-disable`, `@ts-expect-error`, `prettier-ignore`, `fmt: off`, `pragma: no cover`, `istanbul ignore`, `NOLINT`, `nolint`, `shellcheck disable=`, `rubocop:disable`, and more
- compiler and build directives: `//go:build`, `//go:generate`, `{-# LANGUAGE … #-}`, `/// <reference …>`, `/* @__PURE__ */`, `// fallthrough`, Fortran `!$omp`
- secret-scanner allowances (`gitleaks:allow`, `pragma: allowlist secret`, `nosec`), Makefile `##` help text, Dockerfile parser directives
- copyright and license notices; the MIT and Apache licenses require that they stay with copied code

The list errs toward keeping. A false directive keeps one comment; a missed directive deletes something a tool needs. Add a repository's own directives to the config's `allow` list.

Two other things stay out of scope by default:

- **Docstrings** are string literals, not comments. `help()`, Sphinx, doctests, and CLI frameworks read them at run time.
- **Doc comments** (`/** */`, `///`, `//!`, Go comments on declarations, `@param` blocks) feed IDE hovers and generated API docs. The scanner reports them as kind `doc`. Ban them only when the user asks; then classify them like plain comments.

## Phase 0: Settle the run

Detect what you can and propose defaults. Ask the user only about the rest, in one message:

| Setting | How to detect it | Default |
|---|---|---|
| Scope | the user's words | the whole repository |
| Doc comments | the user's words | keep them |
| Issue tracker | `gh repo view`, Linear tools, the tracker named in CONTRIBUTING | ask |
| ADR directory | `docs/adr`, `doc/adr`, `docs/decisions`, `docs/architecture/decisions`, `adr` | `docs/adr/` |
| Lint host | ESLint 9.24 or later in `package.json` → an ESLint rule for JS/TS | the bundled ratchet |
| Where the scanner lives in the repository | an existing `tools/`, `scripts/`, or `bin/` | `tools/comments.py` |
| When a file loses comments | the user's words | CI fails until the lower count is committed; the pre-commit hook commits it for the teammate. The alternative, `--allow-stale`, turns the ratchet into a cap that only `ratchet update` lowers |

Filing issues publishes text outside the repository, so confirm before you file. Commit only when the user asks.

## Phase 1: Inventory and estimate

Define a shell function once, so the command works in bash and zsh. `--no-config` keeps the target repository's uv settings out of the script's own dependency install:

```bash
comments() { uv run --no-config --script "<this skill's directory>/scripts/comments.py" "$@"; }
work=$(mktemp -d)                    # inventory, verdicts, and issue drafts live here
comments estimate src tests          # the numbers, before any edit
comments inventory src tests > "$work/comments.jsonl"
comments inventory src --format tsv | less    # a skimmable view
```

Keep the working files outside the repository, so they do not land in the change. Note the paths you scan: Phase 5 must measure the same paths. Without a path, `estimate` scans the config's `paths` once `.comment-ratchet.json` exists, and the current directory before that.

Without uv, `python3 scripts/comments.py` works when `pygments` is installed.

Give the user the estimate first: it answers "how many lines will this remove" before any work. Report the numbers as the scanner states them:

- **Comment-only lines** are the lines a purge removes. A trailing comment (`x = 1  # why`) shortens a line but removes none.
- **Code lines do not change.** Line counters that skip comments (cloc, tokei, most SLOC metrics) report the same code size after the purge. Do not present comment lines as code shed.
- Check the "skipped as generated" list. A hand-written file with "DO NOT EDIT" near the top is skipped too; exclude it on purpose or fix the marker.
- Check the language list. Configuration files (YAML, TOML) are in scope by default; remove them with `--exclude` or the config's `languages` list if the user wants code only.

## Phase 2: Classify

Classify every `plain` item in `$work/comments.jsonl` (and every `doc` item if doc comments are in scope). For each item:

1. **Read the code it sits on**: the enclosing function's signature and body, about 15 lines on each side. A comment that looks redundant in a list often guards a real constraint three lines down. Never classify from the comment text alone.
2. **Verify every claim** it makes: search for the names it mentions, read the behavior it describes. A false claim makes it stale.
3. **Use the `hints` as leads, not verdicts**: `todo` and `excuse` suggest an excuse, `code` suggests commented-out code, `divider` suggests a tautology.
4. **Review directive prose.** An item with `"prose": true` is a directive with an explanation attached (`# noqa: E501  # the URL cannot wrap`). The directive stays; treat the explanation like a plain comment and edit it by hand if it must go. The scanner keeps every directive, even one that no longer suppresses anything; Ruff's `RUF100` and ESLint's `--report-unused-disable-directives` find those.

Write one JSON line per verdict. Copy the inventory record and add `category`, plus `ref` and `note` where they apply:

```json
{"id": "3f9c0a1b2c4d", "path": "src/billing.py", "category": "excuse", "ref": "", "note": "sleep stands in for the ready event"}
```

`category` is one of `tautology`, `stale`, `excuse`, `decision`, or `keep`. Use `keep` only when the comment must stay and the scanner missed why, such as a directive it does not know. Then add a pattern to the config's `allow` list so the ratchet agrees.

**Large scopes.** Split the inventory by directory and give each part to a subagent with this brief: the policy table, the order of tests, the four steps above, and the verdict format. Then audit a sample of each part yourself. Check every `tautology` that sits on a guard, a lock, a retry, a sleep, a magic number, or an ordering, because those are usually decision records. Also check the evidence behind every `stale` verdict.

Then run `comments estimate --verdicts "$work/verdicts.jsonl"` and show the user the lines per category before you change anything.

## Phase 3: Act

### Excuses: file issues

1. Draft every issue in one file before you file any. One issue covers one defect: merge the excuses that point at the same hack.
2. Search the tracker for an existing issue first, and reuse it.
3. Show the drafts to the user and file them after approval.
4. Put the issue in the verdict's `ref`: a URL, `owner/repo#N`, `#N`, a tracker key such as `ENG-341`, or a file that holds the draft. The `delete` command refuses to delete an excuse without one.

Each issue states:

- what the code does now, and where: path, symbol, and a permalink at the commit before the purge (push it first, or the link breaks; without a remote, give the commit hash and the path)
- the comment, quoted word for word, because the purge removes it from the code
- the fix the comment implies, and what blocks it, if the comment or the history says
- the labels the tracker uses for tech debt

### Decision records: encode or write an ADR

First try to move the fact into the code, where it cannot drift from what it describes:

- **A name**: `timeout_ms` instead of `timeout  # milliseconds`; `MAX_UPSTREAM_RETRIES = 2` instead of `2  # the vendor allows two`.
- **A type**: a `Cents` type instead of `# amounts are in cents`.
- **An assertion** that fails loudly when the assumption breaks.
- **A test** named for the decision, which fails if someone "simplifies" the guard away: `test_retries_stop_after_two_attempts_because_vendor_bans_the_third`. This is the strongest home for a guard, a lock, or an ordering, because the test protects the behavior, not only its explanation.

Do not move prose into a string, an unused variable, or a log message. That is a comment in disguise, and it hides from the ratchet.

When no name, type, or test can carry the fact, write an ADR. [references/adr.md](references/adr.md) has the template, numbering, how to recover the decision's history with git, and how to keep ADRs findable once the code cannot point to them. Merge comments that record the same decision into one ADR.

Put the ADR path, the path of the test or code that now carries the fact, or a URL in the verdict's `ref`. The `delete` command refuses to delete a decision record without a `ref` that exists.

### Delete

```bash
comments delete --verdicts "$work/verdicts.jsonl" --dry-run
comments delete --verdicts "$work/verdicts.jsonl"
```

`delete` removes tautologies and stale comments, and excuses and decision records that have a `ref`. It removes a full-line comment with its line, and a trailing comment with the spaces before it. It never removes a `directive` or `license` item. Before it writes a file, it lexes the result again and requires the same code tokens; for Python it also requires the same AST. It leaves a file unchanged when either check fails, and it reports ids that no longer match because the file changed since the inventory.

Then run the repository's formatter, linter, type checker, and tests. When one fails because of a deletion, restore that file with `git checkout -- <path>`, find the comment the failure depends on, change its verdict to `keep` with a `note` that names the failure (or fix the code it was propping up), and run `delete` again. Watch for:

- **Linters that read comments.** ESLint's `no-empty` accepts `catch (e) { /* ignore */ }` but rejects the empty block once the comment is gone. Fix the code (handle or log the error), not the linter.
- **Blank lines left behind.** Removing a comment between two blank lines leaves two blank lines; the formatter collapses them.
- **Languages pygments lexes imperfectly.** The token check trusts the lexer. For languages other than Python, the build and the tests are the real proof.

### Commits

Split the work so that each commit is easy to review:

1. **Comment deletions only.** The diff touches nothing but comments; the token check guarantees it.
2. **Encodings**: renames, new types, assertions, and tests. These change code, so review them as code.
3. **ADRs.**
4. **The lint rule and the baseline.**

## Phase 4: Ban new comments with a ratchet

After the deletions, record the comments that remain and make the count per file only go down:

```bash
cp "<this skill's directory>/scripts/comments.py" tools/comments.py
uv run --no-config --script tools/comments.py ratchet init src tests --exclude 'src/generated/*'
uv run --no-config --script tools/comments.py ratchet check
```

`ratchet init` writes `.comment-ratchet.json`, which holds the settings and the per-file counts. `ratchet check` fails when a file has more banned comments than its count; it lists them and marks with `(new)` the ones on lines changed since `--base` (default `HEAD`). It also fails when a file has *fewer* comments than its count, until `ratchet update` lowers the baseline in the same change. That rule keeps the baseline tight: a deleted comment cannot be traded for a new one later. ESLint's bulk suppressions and Betterer's CI mode work the same way. The cost is a failed check for a teammate who only deleted a comment, so install the pre-commit hook from the lint reference: it runs `ratchet update` on the staged files, lowers their counts itself, and fails only on a new comment. A renamed file keeps its count under the new path.

[references/lint-rule.md](references/lint-rule.md) shows how to wire the check into pre-commit, CI, and make, the native ESLint rule with bulk suppressions for JS/TS, and the known loopholes.

Prove the rule before you hand it over:

1. Add a comment to a checked file: `ratchet check` fails and marks it `(new)`.
2. Remove it: the check passes.
3. If the baseline still holds comments, delete one: the check fails until `ratchet update` lowers the count. After a complete purge the baseline is empty, so skip this step.

Record the ban itself in an ADR ("Keep decisions in ADRs and tests, not code comments") and point the config's `message` at it, so the failure tells a contributor where the reasoning lives. Add one line to the repository's `AGENTS.md` or `CLAUDE.md` (whichever exists; if neither does, create `AGENTS.md`): before changing a file, search the ADR directory for its path. An agent cannot see a decision that no comment points to unless it is told where to look.

On a large codebase, you can freeze first: run `ratchet init` before any deletion, so no new comments land while the purge is under way, then run `ratchet update` after each batch.

## Phase 5: Report

Measure; do not repeat the estimate. Run `comments estimate` again on the Phase 1 paths and compare. Report:

- comment-only lines before and after, and the difference
- items per category: deleted, encoded, moved to an ADR, filed as an issue, kept
- the issues filed (links) and the ADRs written (paths)
- the comments left in the baseline, by file, and why they are left (not yet classified, decision records waiting for an ADR, and so on)
- the commands that enforce the ban, and where they run (pre-commit, CI)
- the checks run after the deletion (formatter, linter, tests) and their results

## Later runs

This skill is the repeatable process. The baseline lists the files that still hold comments, so it is the worklist for the next run:

```bash
python3 -c "import json; print('\n'.join(json.load(open('.comment-ratchet.json'))['files']))"
```

Run Phases 1 to 3 on those files, then `ratchet update`. To pin the repository's settings for the next run (the scope, the tracker, the ADR directory, the ratchet command), add a short section to the repository's `AGENTS.md` or `CLAUDE.md`. If the team does not install this skill, write a repository-local skill instead, at `.claude/skills/delete-comment/SKILL.md` (or `.agents/skills/` for other agents): the settings, the policy table, the order of tests, and the commands, run against the copy at `tools/comments.py`, so it works without this skill.

## Scanner reference

| Command | What it does |
|---|---|
| `inventory [PATH …] [--kinds plain,doc\|all] [--format jsonl\|tsv]` | One record per comment item |
| `estimate [PATH …] [--verdicts FILE] [--json]` | Lines per kind, the lines a purge removes, and lines per verdict category |
| `delete --verdicts FILE [--dry-run]` | Delete what the verdicts allow, behind the token check |
| `ratchet init [PATH …] [--exclude GLOB] [--ban-doc] [--message TEXT]` | Write `.comment-ratchet.json` with the current per-file counts |
| `ratchet check [FILE …] [--allow-stale] [--base REF]` | Fail on counts above the baseline, or below it |
| `ratchet update [FILE …] [--allow-increase] [--base REF]` | Lower the baseline (for the given files only, in a pre-commit hook) and drop deleted files; raise it only with the flag |

An inventory record has `id`, `path`, `line`, `end_line`, `column`, `language`, `kind` (`plain`, `doc`, `directive`, `license`), `placement` (`full-line`, `trailing`, `inline`), `lines` (the lines a delete frees), `text`, `reason` (why it is a directive, license, or doc comment), `prose`, and `hints`. Consecutive full-line comments at one indentation form one item. The `id` depends on the path, the text, and the order of identical comments in the file; edit a file and its ids can change, so run `inventory` again before `delete`.

The scanner skips binary, minified, and generated files, files over 2 MB, vendored directories (`node_modules`, `vendor`, `third_party`, virtual environments), files with no pygments lexer, and prose or data formats (Markdown, reStructuredText, text, JSON, XML, diffs). `estimate` reports what it skipped and why.

## Related skills

- **comment-slop** judges comments one at a time in a diff or a pull request, and keeps the ones that carry a real why. Use it for review; use this skill for a repository-wide purge with a ban. In a repository that bans comments, comment-slop's "keep" becomes this skill's "encode or ADR".
- **doc-quality** reviews the ADRs you write.
- **linear**, or `gh issue create`, files the excuse issues.
- **test-audit** checks that a test you write to carry a decision protects real behavior.
