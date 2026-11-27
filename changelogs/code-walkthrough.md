# Changelog - code-walkthrough

All notable changes to the code-walkthrough skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.6.1] - 2026-11-26

### Changed
- Statecharts with full labels stay readable: mermaid 10.9.3 keeps each label on one line, so a chart with labels of 4 to 12 words got wide and shrank to fit. The template now breaks each state and arrow label of a `.mermaid[data-statechart]` into lines of at most 26 characters, at spaces, before it renders, as it already drops the chart's `classDef` lines. The page still holds `chart.mmd` unchanged, and other diagrams are not affected. Mermaid 11 wraps labels itself, but it also changes the layout of every flowchart and ER diagram, so the template stays on 10.9.3.

## [1.6.0] - 2026-11-26

### Added
- State models: when the subject has states (a lifecycle, a protocol, a status that the code changes, work that a signal or a second actor can interrupt), or the user asks for a statechart or a flowchart, the explainer adds a flowchart of one run and a statechart that TLC checks through the `statechart` skill. New Phase 2b models the code (before and after for a change), replays each bug path against the real code (reproduced or model only), and models each fix, alternative and simpler design with the same rules, so that each verdict on the page has a report behind it.
- New "Flow and states" section in Phase 3: the two charts and their two jobs, how to read the statechart (states, steps, conditions, parts, regions, and each mark), a walk through one normal run, a rule card for each rule that breaks (the rule, a story, the shortest path, why, how likely, and a toggle of fixes and alternatives, each with its TLC verdict), and simpler designs compared chart to chart. The 30-second version names each broken rule.
- `references/state-models.md`: the procedure, the questions that find a simpler design (two variables that must agree, states the reader cannot tell apart, two owners, a window between two steps), and the Phase 5 checks for these sections.
- Template components: `.mermaid[data-statechart]` (pastes `chart.mmd` unchanged; the JS drops its `classDef` lines, which hard-code light colours with `!important`, and the page colours `breaks`, `mayBreak`, `bugPath`, `repeats` and the group colours in both themes), a chart walker (`data-chartwalk`: each step highlights a state by its id in `chart.mmd`, marks the states before it, keeps the chart at its natural width, and scrolls the state into view after a theme change or a resize), rule cards, and status chips (`breaks`, `may`, `holds`, `reproduced`, `model`).

## [1.5.0] - 2026-11-24

### Added
- Source links. One JSON block in the template (`#walkthrough-source`: the repository URL, the PR number, the merge-base and head SHAs, and the PR's changed files) and `data-path` on each quoted block give every block a link to its line range at the pinned commit (`blob/<sha>/<path>?plain=1#L40-L57`). When the PR changes the file, the block also links to the same lines in the PR's Files changed view (`#diff-<SHA-256 of the path>R40-R57`, or `L` for a Before pane or a diff with only removed lines). The JS builds each link from the line numbers, so a link always covers the lines that its block shows. `.ln` ranges in note lists and test tables link the same way, and a walker with `data-path` gets a header row with its path and links
- The hero links to the PR, and each SHA chip links to its commit
- Phase 0: for a GitHub PR, pin "after" to the PR's head and "before" to the merge base, which the Files changed view compares with
- Phase 5 checks: the pinned head still equals the PR's head; every numbered line matches `git show <sha>:<path>` at its number; each link's range matches its block

### Changed
- `.codehead` styles apply outside `.codewrap`, and the header wraps on a phone

## [1.4.0] - 2026-11-23

### Added
- Line numbers on every quoted block, on by default. The template numbers `.cl` lines from `data-start` on the `<code>`; a `.cl.gap` line marks an elision, has no number, and can restart the count. A unified diff takes `data-old-start` and `data-new-start` from its hunk header: a removed line shows its old number, every other line its new one. A line with its own `data-n` keeps it. The gutter widens for four-digit numbers, and the numbers are generated content, so they are not copied with the code
- File tours (Phase 3): each file that a change adds gets a top-to-bottom read, in which every line appears in exactly one quoted chunk, with a line-keyed note list (`.lbl`, new in the template) under each chunk that links to the mechanism sections. Each test file gets a table of every test, with names and line ranges generated from the file
- Phase 5 checks: every quoted line is numbered; a file tour covers its file with no gap and no overlap; each quoted function or test range starts at its `def`, `class` or first decorator; prose outside code and notes has no line numbers that a re-pin would leave stale; no horizontal scroll at phone width. The render step serves on a free port, reads walker expectations from `data-lines`, skips tab groups in closed `<details>`, and takes element screenshots
- Phase 2: when a stated count comes from a query, check that the query's filter is the same predicate as the code's
- Fidelity rule against line numbers in prose, and pitfalls for re-pinning (a `difflib` line map moves a range that starts on a repeated decorator; remap numbers in one pass, not pair by pair)
- Scaling notes: one owning page per topic in a series; for a change that moves often, one SHA table and one list of facts named by meaning, filled in at assembly

### Changed
- Phase 6: after the user asks for a link, publish again to the same URL after each rebuild that passes Phase 5

### Fixed
- The walker clipped its step text and "next" button on a phone: the one-column layout used `1fr`, which grows to the widest code line. It now uses `minmax(0, 1fr)`
- With more than about ten steps, the walker's dots pushed "next" off the card. The dots now wrap
- In a long walker, the highlighted lines could be off screen. The code pane now has a maximum height and scrolls itself (never the page) to the first highlighted line at each step
- Long inline identifiers in prose, lists, tables and the glossary widened the page on a phone. They now wrap with `overflow-wrap: break-word`
- Two tab groups under one parent switched each other's panes when one group's name was a prefix of the other's (`fix` and `fix2`). A pane now belongs to the group whose button has its key

Prompted by feedback from a change explainer for a data-repair pull request (`notes/code-walkthrough/2026-11-23-pr-explainer-feedback.md`). The template changes were checked in a headless browser at 1280 px and 390 px, in both themes. The feedback's shipped build script (directives, symbol anchors, a re-pin command) is not part of this release.

## [1.3.0] - 2026-11-18

### Added
- Code explainers: the skill now also teaches how existing code works (a subsystem, feature, mechanism, or flow), not only a change. A table in "Two kinds of explainer" lists what differs: one pinned commit instead of before and after refs, a 30-second version that states what the code does and what a change must keep, units in request order, and a "Before you change it" section in place of the reviewer checklist. A topic outside the repository uses the same pipeline and cites its source
- "Related skills" section: `mermaid-cli` validates diagram source in Phase 4; the Playwright MCP tools, `playwright`, `dev-browser`, or `chrome-cdp` drive Phase 5; `dataviz` draws charts; `show-me` hands explainer files to this skill
- Phase 4 fidelity rule: validate each diagram with `mmdc` before it goes into a fragment

### Changed
- The description triggers on any request for an explainer HTML file, page, or document, and says to use this skill instead of `show-me` or a hand-written page for one
- Phase 6: the deliverable is the local file; publish it as an Artifact only when the user asks for a link

### Fixed
- Phase 5 passed a diagram with a syntax error: mermaid draws the error as an SVG ("Syntax error in text"), so "every `.mermaid` contains an `svg`" was true. The check now also requires that no SVG has `aria-roledescription="error"`, and notes that `mmdc` and the template's mermaid 10.9.3 can disagree on newer syntax

## [1.2.0] - 2026-11-16

### Added
- Prose rules for the generated document. Three rules do separate jobs, and the SKILL.md intro names them:
  - **Understanding over economy** selects the content. It asks for the why of each before/after, one traced example per mechanism, enough code to follow the change, terms defined at first use, and facts restated instead of assumed. It also asks for captions on diagrams, one idea per section, and a split into a series instead of shorter explanations. It names the padding to delete.
  - **Bottom line up front (BLUF)** sets the order at each level: the document, each section, each paragraph, and each before/after, walker step, callout, and caption. A bottom line uses only terms that an earlier section taught, so BLUF keeps the spiral order.
  - **ASD-STE100** controls the words: one idea per sentence (20 words for an instruction, 25 for a description), complete sentences, active voice with a named actor, simple tenses, one word for one meaning, and literal verbs. Technical names are permitted. A style rule must not delete a fact.
- Phase 5 read-through: check that each section opens with its point, that no term comes before its definition, and that each before/after says why. Flag prose sentences over 25 words.

### Changed
- The 30-second version states what changes, why, and what the reviewer must check.
- The template's section example opens with a bottom-line paragraph, and the slot comment points to the prose rules.

## [1.1.0] - 2026-11-16

### Added
- Syntax highlighting: put `class="language-<name>"` on a code block's `<code>` (or a `.sig` box) and highlight.js 11.12.0 colours it at load. It highlights the whole block as one text, then splits the HTML back onto the `.cl` lines, so `add`/`del`/`hl`/`dim` classes and walker `data-l` attributes survive, and multi-line strings and comments stay coloured on every line. Grammars outside the common bundle load on demand. A block with no language, or with markup inside a line, is left as written
- Token palette as CSS variables (`--tk-*`) for both themes, shared by highlight.js classes and the hand-marked `.kw`/`.str`/`.cmt` spans. Every token colour passes WCAG AA (4.5:1) on code, added, removed, and highlighted lines
- Themed mermaid diagrams: the `base` theme gets `themeVariables` read from the page's CSS colours, and every diagram re-renders when the theme changes. The 1.0.0 workaround kept a light canvas in dark mode
- `class NodeId current` in a flowchart highlights that node in both themes (for the chain-map "you are here" node)

### Changed
- The theme is set by an inline script in `<head>` before first paint (no light flash for dark-mode readers), follows OS changes until the reader picks one, and sets `color-scheme` so scrollbars and form controls match. The toggle button now names the theme it switches to
- Diagrams render off-screen and swap in, so a re-render never shows raw source
- Walker buttons use dark text on the accent colour in dark mode (white was 2.76:1)
- SKILL.md: authoring rules for `language-*` and for diagram colours, browser checks for highlighting and diagram re-theming, rewritten dark-mode pitfall, and a new pitfall on highlighters that flatten per-line markup
- Phase 6 now names two CDN dependencies (mermaid and highlight.js); offline the document degrades to plain code and diagram source

### Fixed
- The template's slot documentation comment ended early at the mermaid example's `-->` arrow, so a page that kept the comment rendered the rest of the docs (including a stray glossary list), and a regex that stripped the comment stopped at that arrow
- Code blocks rendered a blank line after every line: the newline between two block-level `.cl` spans displayed as an empty line. Empty `.cl` lines keep their height
- Diagrams inside a hidden before/after pane or a closed `<details>` rendered broken (clipped notes, missing actor boxes); off-screen rendering gives them a real layout
- Tab, walker, and theme buttons used `font: … inherit`, an invalid shorthand the browser dropped, so they fell back to the default button font (Arial)
- Walker code took the inline-`code` style (smaller font, padding, background) instead of the code-block style
- A code block without `.cl` lines had no left padding

## [1.0.0] - 2026-07-29

### Added
- Initial skill: create self-contained interactive HTML documents that teach a code change (branch, PR, diff, or subsystem) to a reviewer with no prior knowledge
- 6-phase pipeline: extract (read-only agent fan-out with exact git refs, verbatim-first) → verify (author independently re-checks every critical claim) → structure (spiral pedagogy: BLUF → foundations → mechanism → per-unit walkthroughs → flows → scope boundaries → reviewer checklist → glossary) → author (fragments + concatenate) → browser-verify (structure checks, render checks, light/dark screenshots) → deliver (single file, fragments kept for iteration)
- Component library: sidebar TOC with scrollspy, before/after code toggles, diff-colored code lines, collapsible deep-dives, step-through code walker with line highlighting, mermaid diagrams, callouts, glossary-linked terms, light/dark theme, playground widgets that mirror the logic under study
- `references/template-shell.html`: generic, domain-agnostic HTML shell with the full CSS/JS component library and inline usage documentation for every component
- Pitfalls section from production use: mermaid dynamic-import timing (startOnLoad never fires → explicit `mermaid.run()`), dark-mode diagram canvas stays light, empty-grep false negatives (wrong-cwd), agent-claims-are-leads-not-facts, cwd discipline during assembly
