# code-walkthrough feedback: a change explainer for a data-repair PR

**Date:** 2026-11-23
**Skill:** `code-walkthrough` 1.3.0 (`plugins/code-walkthrough/skills/code-walkthrough/SKILL.md`, `references/template-shell.html`)
**Subject:** a change explainer for a pull request in a private repository. The PR adds one data-repair job (a ~590-line
Python file), its test file (~950 lines, 49 tests), a CSV of overrides and a job manifest. It adds no other file.
**Outcome:** the page shipped and passed every check, but the user gave two pieces of feedback that the skill should have
prevented: "the code needs line numbers", and "it doesn't do a good job of walking through the code in the PR". The page
also needed seven re-pins in one day as the PR moved, and each re-pin was manual and error-prone.

## Bottom line

1. **Line numbers must be a default.** The template draws code with no line numbers, and nothing in SKILL.md asks for
   them. A reviewer cannot map a note such as "the check at the top of `_run`" to the file. Add line numbers to the
   template and to the component table (details in [1](#1-no-line-numbers)).
2. **A PR that adds files needs a top-to-bottom read of each file.** Phase 3 sends the author to "per-unit walkthroughs:
   file-by-file before/after". For an added file there is no "before", so the author organizes by mechanism, and each
   section quotes a slice of a function. No section reads the new file in order. Add a "read the file" tour for added
   files, with a coverage check (details in [2](#2-no-linear-walk-through-of-the-prs-code)).
3. **Re-pinning to a new head is the most expensive step, and the skill has no tool for it.** Line ranges, SHAs, counts
   and widget constants are all hard-coded in the fragments. Ship a build script with symbol anchors and a facts file
   (details in [3](#3-re-pinning-when-the-pr-moves) and [4](#4-numbers-that-change-are-scattered-through-the-prose)).
4. **The template has layout bugs on phones and with long walkers.** Small CSS and JS fixes (details in
   [5](#5-template-shell-bugs)).

## Context: what was built

- A single HTML page from fragments, built by a `build.py` copied from an earlier explainer (the skill ships no build
  script). The build expands directives so quoted code stays verbatim:
  - `<!--CODE path="..." lines="10-20,30-35" hl="12"-->`: a code block from a pinned snapshot, with a marked elision
    between ranges.
  - `<!--DIFF patch="..." file="..." hunks="2,3"-->`: Diff / Before / After tabs from one file of a `.patch`.
  - `<!--WALK segs="path:a-b|path:c-d"-->`: walker code lines with `data-l="<seg>.<line>"` keys.
  - `[[src:path:a-b|label]]`: a link to GitHub at the pinned SHA.
- Over the day the page grew to 32 fragments (~466 KB): foundations, one section per mechanism, a 16-step walker, a
  JS playground that ports the job's decision logic, five diff-tab groups, four mermaid diagrams, an 11-question quiz,
  a glossary, and finally a six-section code tour.
- Checks that ran on every rebuild: tag balance, anchor resolution, tab/pane pairing, mermaid via `mmdc`, a headless
  Chromium run (36 assertions: diagrams, highlighting, walker, tabs, playground cases, quiz, dark theme, phone overflow,
  console errors, line numbers), and a prose check (sentences over 25 words, `-ing` forms).

The PR head moved seven times in one day: two fix commits, a column removal, a performance commit, a manifest change,
a rebase onto a newer base (which changed every commit SHA), review fixes, and a rule change. Every move meant a re-pin.

## What worked

- **Directives over hand-written code.** Quoting by line range from a `code/` snapshot (fetched with
  `gh api -H "Accept: application/vnd.github.raw" repos/<o>/<r>/contents/<path>?ref=<sha>`) removed escaping bugs and
  made "verbatim" mechanical. The build fails on a bad range.
- **`mmdc` before the page.** It caught every diagram error before the browser did.
- **The playground as a port of the real logic.** Each option linked to the line that decides it. The browser check
  drove 16 input combinations through it and compared the outcome with the code's.
- **The quiz.** Cheap to write, and its explanations link back to sections, so it doubles as an index.
- **Phase 2 (verify).** It caught real errors, for example a count that came from a query whose predicate differed
  from the code's (see [6](#6-verify-counts-against-the-codes-predicate-not-the-querys)).

## 1. No line numbers

**What happened.** Every code block showed code with no line numbers. The user asked for them after the page shipped.

**Why the skill missed it.** The component table lists "Diff-colored lines", "Syntax highlighting" and the walker, but
not line numbers. The template's `.cl` lines carry `data-l` only for walkers.

**What fixed it.** A `data-n` attribute on every `.cl` line, set by the build, and a CSS counter-free `::before`:

```css
.cl[data-n]::before { content: attr(data-n); display: inline-block; min-width: 3ch; margin: 0 12px 0 -6px;
  text-align: right; color: var(--ink-3); opacity: .75; user-select: none; -webkit-user-select: none; }
.cl.dim:not([data-n])::before { content: ""; display: inline-block; min-width: 3ch; margin: 0 12px 0 -6px; }
```

- The highlighter in the template replaces only each line's `innerHTML`, so `data-n` survives highlighting.
- `user-select: none` keeps numbers out of a copy.
- Diff tabs need a rule: number Before lines from the old file and After lines from the new file. In the Diff tab, use
  the old number for a removed line and the new number for the others. Read the start numbers from each hunk header
  (`@@ -a,b +c,d @@`).
- Elision lines get no number, but keep the gutter width.

**Recommendation.** Put `data-n` and this CSS in `template-shell.html`, show it in the "Code with diff colors" example,
and add a row "Line numbers (on by default)" to the component table. Add a browser check: every non-elision `.cl` line
has a number.

## 2. No linear walk-through of the PR's code

**What happened.** The page explained the job by mechanism: which rows it selects, its parameters, its rules, one
org step by step, the two writes, undo, reruns, logs. Each section quoted the slice of code it needed. The user said the
page "doesn't do a good job of walking through the code in the PR".

**Why the skill led there.** Phase 3 step 4 says "per-unit walkthroughs: overview → file-by-file before/after →
subtleties → tests". For a file the PR adds, there is no "before". So the author falls back to concept sections, and
nothing forces a read of the new file in order. The walker (one execution path) and the diff tabs (one commit) did not
fill the gap either.

**What fixed it.** A "Read the code" part, placed after the foundations and before the mechanism sections:

- Six sections that read the job file from line 1 to the last line, in order: setup, the class and its inputs,
  evidence helpers, the main per-item function, the writes, and the tests.
- Each chunk is one function or one coherent block, quoted in full (no elisions), with line numbers.
- Under each chunk, a list of notes keyed by line range ("355-359: an item with no recorded type is skipped and
  logged…"). Each note links to the mechanism section that explains it in depth.
- Imports and the long class docstring sit in a collapsed `<details>`.
- The test file gets its own tour: the setup and helpers line by line, then one table per test group with every test
  (linked to its line range), what it sets up, and what it checks. A small script generates the tables from the test
  file, so the line ranges cannot drift; only the "sets up / checks" text is written by hand.

The note-list style that worked:

```css
.lbl { list-style: none; padding-left: 0; margin: 8px 0 18px; }
.lbl li { margin: 6px 0; padding-left: 92px; text-indent: -92px; }
.lbl li > .ln { display: inline-block; width: 84px; text-indent: 0; margin-right: 8px;
  font: 600 12.5px ui-monospace, Menlo, monospace; color: var(--accent-ink); }
@media (max-width: 600px) { .lbl li { padding-left: 0; text-indent: 0; } .lbl li > .ln { display: block; width: auto; } }
```

**Recommendation.**

- In Phase 3, add: "For each file the change adds, write a top-to-bottom tour: every line of the file appears in
  exactly one quoted chunk, in file order, with a line-keyed note list. For each test file, list every test with what it
  sets up and what it checks." Keep the mechanism sections; the tour links into them.
- Add a coverage check to Phase 5: the union of the tour's `CODE` ranges for an added file equals `1..len(file)`, with
  no overlap.
- Add the note list (`.lbl`) to the template and the component table.
- In the "Two kinds of explainer" table, the change-explainer "Units" row should say what to do for added files.

## 3. Re-pinning when the PR moves

**What happened.** Each new head needed the same manual steps:

1. Fetch the changed files into `code/` and keep the old copies.
2. Remap every line reference in `CODE`, `WALK`, `data-lines` and `[[src:]]` from the old file to the new one. A
   `difflib.SequenceMatcher` over the two versions gives a line map.
3. Update link labels that repeat a range ("test lines 194-212").
4. Update prose that names line numbers ("the comment at lines 111-112").
5. Update SHAs in prose, the hero, the build constants and each diff tab's before/after labels. A rebase changes every
   commit SHA, so all of them change at once.
6. Update the line numbers hard-coded in the playground JS (the "decided at line N" links).

**What went wrong.**

- **Ambiguous anchors.** The difflib map is wrong for ranges that start on a line that repeats in the file. In a test
  file, a shared decorator such as `@pytest.mark.django_db` precedes almost every test, so a range that started on it
  was mapped onto another test's decorator. Four quotes and links pointed at the wrong test until a check printed the
  first line of every quoted test range.
- **Chained replacements.** Remapping JS constants one pair at a time turned `[243, 244] → [245, 246]` and then the new
  `[245, 246] → [247, 248]`. A one-pass regex with a lookup table fixed it.
- **Prose line numbers.** Plain text such as "lines 111-112" is invisible to directive remapping. Two went stale before a
  grep caught them.

**Recommendation.** Ship the build script with the skill (in `references/`), and give it a re-pin command:

- **Symbol anchors.** Allow `lines="_run+0..+16"` or `[[src:path:RepairJob._run]]`, resolved by parsing the file (for
  Python, `ast` gives each function's start and end lines). Symbol anchors survive most edits without a remap.
- **Validate quoted ranges.** Warn when a range for a function or test does not start at its `def` or its decorator.
- **No hand-written line numbers in prose.** Offer a `{{lines:Symbol}}` placeholder that the build expands, and make the
  prose check flag `lines? \d+` outside directives.
- **Widget constants from the build.** Emit a small JSON of anchor → line range into the page, so a playground reads
  "decided at" lines from it instead of hard-coding them.
- **One SHA table.** Keep head, base and per-commit SHAs in one place, and expand them everywhere (hero, labels,
  links, prose).

## 4. Numbers that change are scattered through the prose

**What happened.** A rule change moved four counts. The same figures appeared in about 20 places across both pages.
Worse, one figure meant two different things: the size of a class in the data (unchanged) and the number of items the
job skips (changed). Each occurrence needed a human decision.

**Recommendation.** Add a facts file (`facts.json`) and a placeholder (`{{fact:job.no_evidence}}`) to the build. Name
facts by meaning, not by value, so two different quantities that happen to be equal stay separate. The build fails on
an unknown fact.

## 5. Template shell bugs

All four were found by the phone-width and long-content checks, and all four have small fixes.

| Bug | Fix |
|---|---|
| On a narrow screen the walker's single `1fr` column grows to the widest code line, so the step text and the "next" button are clipped. | `@media (max-width: 900px) { .walker { grid-template-columns: minmax(0, 1fr); } }` |
| With more than ~10 steps the walker dots push "next" off the card. | `.walker .wdots { flex: 1 1 auto; min-width: 0; flex-wrap: wrap; justify-content: center; }` |
| A long walker code pane (120+ lines) leaves the highlighted lines off screen. | `max-height` + `overflow-y: auto` on `.wcode`, and after each prev/next, scroll the pane to the first `.cl.hl`. |
| Long inline identifiers (test names) widen the page on phones. | `p code, li code, td code, dd code, dt, .caption code { overflow-wrap: break-word; }`. `anywhere` breaks names mid-word in tables; `break-word` does not. |

Also worth documenting in the template comments: the tab script scopes panes by the tabs' parent element, so each tab
group needs its own wrapper element.

## 6. Verify counts against the code's predicate, not the query's

A page stated how many rows of one kind the job selects. The figure came from a data query whose filter for "open" rows
had one condition. The job's filter has two, so it selects only about a quarter of those rows. Phase 2 says "if the doc
will state a number, count it yourself"; it should add: "and check that the count uses the same predicate as the code".

## 7. Two pages on one topic drift apart

The topic had an earlier investigation page and the new PR page. The older page kept its own copy of the job section,
which went stale (old head, a removed CSV column described as an open decision). The user asked which page was
authoritative.

**Recommendation.** Add to the scaling notes: in a series, each topic has one owning page. Other pages summarize it in a
few lines and link to it. They do not keep a second copy of its code walkthrough.

## 8. Smaller items

- **Browser check fragility.** A fixed server port collided with a stale server and the checks read a 404 page; bind to
  port 0. Hard-coded expectations ("walker step 1 lights line 274") broke on every re-pin; derive them from the
  fragment. `page.screenshot(clip=…)` fails for elements below the fold; use `locator.screenshot()`. Tab groups inside a
  closed `<details>` are not clickable; skip hidden groups.
- **The prose checker.** A sentence that starts with an identifier (`_repair checks…`) is not split, so it reports false
  "over 25 words" hits. Ship the checker as a script with the skill, with an identifier-aware splitter.
- **Sources outside the repository.** The page quoted SQL and a shell recipe from the author's notes. The build needed a
  source prefix with no GitHub link. Support this in the shipped build.
- **Publishing.** SKILL.md says to deliver a local file and publish only on request. This user wants every explainer
  published to a fixed URL after each rebuild. A configurable "publish" step (a command run after a clean check) would
  cover both.
- **Size.** The page reached ~466 KB with 32 fragments. The scaling notes suggest a series; a code tour is a natural
  candidate for its own page when the mechanism sections are long.

## Proposed changes, in priority order

1. `template-shell.html`: line numbers (`data-n` + CSS), the `.lbl` note list, and the four layout fixes in [5](#5-template-shell-bugs).
2. `SKILL.md` Phase 3: the "read the file" tour for added files and the test tour; Phase 5: tour coverage and
   line-number checks; Phase 2: the predicate rule in [6](#6-verify-counts-against-the-codes-predicate-not-the-querys).
3. Ship `references/build.py` with `CODE` / `DIFF` / `WALK` / `src` directives, symbol anchors, a SHA table, a facts
   file and a re-pin command.
4. Ship the browser and prose check scripts.
5. Scaling notes: one owning page per topic; consider the code tour as its own page.
