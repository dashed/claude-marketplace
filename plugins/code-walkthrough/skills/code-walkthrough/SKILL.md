---
name: code-walkthrough
description: "Create a self-contained interactive HTML document that teaches a code change (branch, PR, diff, or subsystem) to a reviewer with no prior knowledge — with before/after code toggles, mermaid diagrams, step-through walkthroughs, and playground widgets. Use when the user wants to learn or review a code change interactively, asks for a walkthrough/teaching/review document of a branch or PR, wants before/after explanations with visuals, or mentions interactive HTML docs, mermaid walkthroughs, or teaching a codebase area from zero."
license: MIT
---

# Code Walkthrough

Produce ONE self-contained interactive HTML file that teaches a code change from zero prior knowledge. The reader finishes able to review the change line-by-line: what each module does, why the seams are where they are, what the failure modes are, and what to scrutinize.

The output is a teaching document, not a diff dump. Code is quoted verbatim; understanding is built in layers; interactivity does real pedagogical work (toggles for before/after, walkers for execution order, playgrounds for logic under study).

## When to Use

- "Walk me through this branch/PR/diff (before/after) in an HTML file"
- "I want to learn/review this change effectively — make it interactive, with diagrams"
- "Teach me this subsystem from zero" (with code as the source of truth)

## The Pipeline

Follow these phases in order. Phases 1–2 protect fidelity; phases 3–4 build the document; phase 5 proves it works.

### Phase 0 — Frame

1. Pin the exact refs that define **before** and **after** (branch tips, PR base/head, commit range). Write them into the document later — every code claim must trace to a ref.
2. Define the audience contract: "no prior knowledge" means no knowledge of *this domain and this codebase* — include a glossary of domain terms, but do not teach the programming language.
3. Identify the 1–3 **core mechanisms** the change builds on (pre-existing patterns the reader must understand first). These get their own foundations sections before any diff is shown.

### Phase 1 — Extract (fan out, read-only)

Extraction parallelizes well; use subagents for independent units (one per branch/module/ring of context). Rules for every extractor:

- **Read-only**: use `git show <ref>:<path>` / `git diff <a>..<b>` / `git grep <pat> <ref>`. Never check out branches, never modify files, never run the repo's test suite (respect host-repo constraints — e.g. shared test databases, single-runner rules).
- **Verbatim-first**: demand full function bodies, complete diffs, full commit bodies — "do not paraphrase code". Line anchors (`file.py:123`) for every claim.
- Ask each agent for: commit list with bodies, diff stat, per-file verbatim diffs, full tip content of key regions, the "before" state of the same regions, test inventory with the load-bearing tests quoted, and the subtleties *with evidence*.

### Phase 2 — Verify (the phase that makes the doc trustworthy)

Never bake agent output into the document unverified. Independently re-read every critical block yourself at the exact refs: the star functions, the before/after of the core change, anything surprising. Agent reports are leads, not facts — expect a couple of wrong or stale claims per batch and catch them here. If the doc will state a number (test counts, line counts), count it yourself.

### Phase 3 — Structure (spiral pedagogy)

Order the document so each section only needs what came before:

1. **Hero** — title, scope chips (refs, sizes, commit counts)
2. **The 30-second version** — what changes, in plain language, with a map diagram
3. **Foundations** — domain 101, the wire contracts/interfaces, the core mechanisms (this is where "the X stuff" gets taught when the user asks "teach me X too")
4. **Per-unit walkthroughs** — one per branch/module: overview → file-by-file before/after → subtleties → tests
5. **End-to-end flows** — sequence diagrams that tie the units together
6. **Scope boundaries** — what this change deliberately does NOT do, and where that lives
7. **Reviewer checklist** — invariants, who enforces them, what would break them; questions to ask
8. **Glossary + appendix** — every domain term; the road-not-taken; full listings of anything condensed earlier

### Phase 4 — Author (fragments + components)

Write the document as fragment files, then concatenate in order. This keeps a 1500-line file editable and lets you fix one section without rewriting all of it. Copy [references/template-shell.html](references/template-shell.html) — it contains the full CSS theme and the JS for every component below, with `<!-- @SLOT -->` markers showing where content goes.

**Component library** (all wired in the template; use them, don't reinvent):

| Component | Use for |
|---|---|
| Sidebar TOC + scrollspy | navigation in long docs |
| Before/after tab toggles | every meaningful diff — reader flips between base and tip |
| Diff-colored lines (`.cl.add/.cl.del/.cl.hl`) | real diffs (add/del) and attention (hl = not a diff!) |
| Syntax highlighting (`<code class="language-python">`) | every code block — highlight.js colours the tokens and keeps the per-line diff/walker classes |
| Collapsible `<details>` deep-dives | side context that would interrupt the spiral |
| Step-through walker | execution-ordered code (a write path, a state machine) — steps highlight line ranges |
| Mermaid diagrams | chain maps, ER diagrams, dependency graphs, sequence diagrams, state transitions |
| Callouts (`.note/.warn/.key`) | the one idea per section the reader must not miss |
| Glossary-linked `<dfn>` | domain terms, clickable to the glossary |
| Light/dark theme | follows the OS until the reader toggles (then persisted); set before first paint; code tokens and diagrams re-theme too |
| Playground widgets | mirror the logic under study in JS (a validator the reader can throw inputs at, a scheduler that shows race outcomes) — the strongest teaching tool when the domain allows |

**Fidelity rules:**

- Quote code **verbatim** at stated refs. If you condense, mark it ("condensed for width", elision comments) — never silently alter.
- HTML-escape everything (`<=` → `&lt;=`); run the balance check in phase 5 to catch what you missed.
- `add`/`del` colors only for lines that are actually added/removed in the diff; use `hl` for emphasis elsewhere.
- Put `language-<name>` (a highlight.js name or alias: `python`, `ts`, `tsx`, `go`, `sql`, ...) on every code block's `<code>`. Keep lines plain text — no `+`/`-` prefixes, no spans inside a `.cl` line; a line with markup in it opts its whole block out of highlighting.
- No hard-coded colours in mermaid source (`style X fill:#…`, coloured `classDef`): they break in one of the two themes. Mark the node the reader should look at with `class NodeId current`.
- No planning artifacts, ticket IDs, or local scratch paths in the document unless the user asks for them.

### Phase 5 — Verify in a real browser

1. **Structure**: parse the HTML (any lenient parser) for unbalanced tags; check every `href="#…"` resolves; check tab buttons match panes; count mermaid blocks.
2. **Render**: serve the file (`python3 -m http.server`) and drive a headless browser (e.g. the Playwright MCP):
   - every `.mermaid` contains an `svg` (count them)
   - every `code[class*=language-]` block contains `.hljs-*` spans and still has its original number of `.cl` lines
   - walker: click next/prev, assert the active step and highlighted lines change
   - tabs: toggle each group, assert pane visibility flips
   - theme: toggle dark, assert the diagram SVGs were replaced (new `svg` ids) and re-check readability of diagrams and code
   - playgrounds: exercise them via `evaluate` (set input, assert verdict output)
   - console: no errors (a favicon 404 is fine; a 404 for `…/languages/<name>.min.js` means a `language-` name highlight.js does not know)
3. **Screenshots** in light AND dark of the hero, one diagram-heavy section, and each custom widget — look at them yourself; rendering bugs hide in screenshots, not in DOM assertions.
4. Fix and re-check until clean. Delete screenshots and kill the server when done.

### Phase 6 — Deliver

Deliver the single HTML file at the requested path. Keep the fragments directory (mention it — it is how the user iterates). Note the two external dependencies (mermaid and highlight.js, both from the jsDelivr CDN) and that offline the document degrades to plain code and readable diagram source. If the user is currently reading an earlier document, write a NEW file and cross-link; never edit a file the user has open.

## Pitfalls (learned the hard way)

1. **Mermaid + dynamic import**: `mermaid.initialize({startOnLoad: true})` silently never renders when the import resolves after the load event. Use `startOnLoad: false` + explicit `await mermaid.run({querySelector: ".mermaid"})`, with a fallback that swaps diagrams for their (readable) source text if the CDN is unreachable.
2. **Dark-mode diagrams**: mermaid's stock themes are fixed palettes; the neutral theme draws dark text, invisible on a dark page. The template uses the `base` theme with `themeVariables` read from the page's CSS colours, and re-renders every diagram when the theme changes. It renders off-screen and swaps the SVG in, because rendering in place shows raw source mid-render, and a diagram inside a hidden tab or closed `<details>` lays out broken (clipped notes, missing actor boxes).
3. **Highlighters flatten line markup**: `hljs.highlightElement` and similar re-read `textContent` and replace the block, destroying the `.cl` line spans that carry diff colours and walker line numbers. The template highlights the joined text and splits the HTML back onto the lines, closing and re-opening any span (a multi-line string or comment) that crosses a newline.
4. **Empty grep false negatives**: an empty result from a tree-wide search proves nothing if you were in the wrong directory. Sanity-grep a term you KNOW exists first; check `pwd` after hopping between repos.
5. **Agent claims ≠ facts**: the two classic failures are plausible-but-wrong mechanism descriptions ("the setting lives in an org option" — actually a model column) and unverified counts ("12 tests" — actually 7). Phase 2 exists for this; do not skip it when the agents sounded confident.
6. **`order_by` vs in-Python sort** (and similar framework subtleties): when the code comments explain a non-obvious choice, quote the comment — it is usually the reason the reader was confused.
7. **cwd drift**: assembling fragments or running validation from the wrong working directory produces confusing "file not found" storms. Use absolute paths in assembly commands.

## Scaling notes

- Small change (≤3 files): skip agent fan-out; extract directly, still follow phases 2→5.
- Multi-branch stacks: one document per 1–2 branches, cross-linked in a series — better than one 4000-line document. Give each part a chain-map diagram with the current part highlighted (`class NodeId current`).
- Keep widgets honest: a playground must implement the same logic as the code it teaches (port the checks, don't fake outcomes), and say so in the document.
