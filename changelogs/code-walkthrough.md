# Changelog - code-walkthrough

All notable changes to the code-walkthrough skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
