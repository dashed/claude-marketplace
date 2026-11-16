---
name: code-walkthrough
description: "Create a self-contained interactive HTML document that teaches a code change (branch, PR, diff, or subsystem) to a reviewer with no prior knowledge — with before/after code toggles, mermaid diagrams, step-through walkthroughs, and playground widgets. Use when the user wants to learn or review a code change interactively, asks for a walkthrough/teaching/review document of a branch or PR, wants before/after explanations with visuals, or mentions interactive HTML docs, mermaid walkthroughs, or teaching a codebase area from zero."
license: MIT
---

# Code Walkthrough

Produce ONE self-contained interactive HTML file that teaches a code change from zero prior knowledge. The reader finishes able to review the change line-by-line: what each module does, why the seams are where they are, what the failure modes are, and what to scrutinize.

The output is a teaching document, not a diff dump. Code is quoted verbatim; understanding is built in layers; interactivity does real pedagogical work (toggles for before/after, walkers for execution order, playgrounds for logic under study).

**Aim for understanding over economy.** Put the bottom line first, and write in ASD-STE100. The [prose rules](#prose-rules) give the details.

## When to Use

- "Walk me through this branch/PR/diff (before/after) in an HTML file"
- "I want to learn/review this change effectively — make it interactive, with diagrams"
- "Teach me this subsystem from zero" (with code as the source of truth)

## Prose rules

Three rules control all prose in the document: body text, captions, callouts, walker steps, and glossary entries. Each rule has a different job. Rule 1 selects the content. Rule 2 sets the order. Rule 3 controls the words. Quoted code and quoted code comments stay verbatim, so these rules do not apply to them.

### 1. Aim for understanding over economy

If a shorter text would be less clear, write the longer text. The reader does not know this domain or this codebase, so the reader cannot fill a gap. A step that you skip to save space is a step that the reader cannot make. Use one test for each section: after one read, can the reader explain it back? The length of the section is not the test.

- **Say why, not only what.** For each before/after, state:
  - what the old code did, and what problem it had
  - what the new code does
  - why the author chose this design over the obvious alternative
- **Trace one real example.** Follow one concrete value (a request, a row, an event) through each mechanism, from input to output. When the tests have values, use them.
- **Show enough code.** Quote the full function when the reader needs its context to follow the change. Remove only the lines that the reader does not need, and mark each removal. A hunk without its caller is not enough.
- **Define each term at its first use** in a short clause, and also in the glossary. The reader must not need the glossary to read a sentence.
- **Restate facts. Do not trust the reader's memory.** When a section uses a fact from an earlier section, restate the fact in one sentence. Link to the section that teaches it.
- **Give each diagram and widget a caption** that says where to look and what it shows. A diagram adds to its paragraph. It does not replace the paragraph.
- **Teach one idea in each section.** Do not merge two mechanisms to save a heading.
- **Split the document, do not cut it.** If the document becomes too long, split it into a cross-linked series (see [Scaling notes](#scaling-notes)). Do not make the explanations shorter.

Understanding is not length. Some text adds words and removes understanding, so delete it:

- a point said again in different words
- a description of what a line of syntax does
- lessons on the programming language (Phase 0 excludes them)
- an introduction before the point

This rule also applies to the work behind the document. Read the full function and its callers before you explain a hunk. An explanation of code that you only skimmed is short because it is shallow.

### 2. Bottom line up front (BLUF)

Put the conclusion first at each level. Put the support after it.

- **Document.** The "30-second version" comes immediately after the hero. It states what changes, why, and what the reviewer must check. A reader who stops there has the answer.
- **Section.** The first paragraph states the point of the section in one to three sentences. The code, the diagrams, and the detail come after it. Keep `h2` titles short for the sidebar. Put the point in the first sentence, not in the title.
- **Paragraph.** The first sentence states the topic.
- **Before/after, walker step, callout, caption.** The first sentence states what changes or what the step does.

BLUF does not break the spiral order of Phase 3. A bottom line uses only plain words and terms that an earlier section taught. The section then teaches what its bottom line needs.

### 3. Write in ASD-STE100 (Simplified Technical English)

Use the STE rules. STE permits technical names, so code identifiers, file paths, and the domain terms in the glossary are correct words.

- **One idea in each sentence.** Use a maximum of 20 words in an instruction and 25 words in a description. Use a maximum of six sentences in a paragraph. Use a vertical list for three or more items or conditions.
- **Complete sentences.** Keep the articles. Do not write verbless fragments such as "Retries on failure."
- **Active voice with a named actor.** Write "The scheduler retries the job", not "The job is retried". In a code explanation, the actor is often the important fact: it tells the reader which layer does the work.
- **Simple tenses.** Use the present tense for what the code does. Use the past tense only for what the old code did before the change.
- **One word, one meaning.** Use the identifier or the glossary term each time. Do not change the word for variety, because the reader will think that a new word is a new thing.
- **Literal verbs.** Code does not "consult", "answer", or "follow" a rule. Say what it does: it reads, returns, calls, or writes.
- **No `-ing` forms, no double negatives, no idioms.** Technical names are the exception.

**A style rule must not delete a fact.** STE makes sentences shorter, not explanations. If an explanation needs 60 words, write three sentences of 20 words. If a rule and a fact conflict, keep the fact. Rule 3 serves rule 1, not the reverse.

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
2. **The 30-second version** — the bottom line: what changes, why, and what the reviewer must check, in plain words, with a map diagram
3. **Foundations** — domain 101, the wire contracts/interfaces, the core mechanisms (this is where "the X stuff" gets taught when the user asks "teach me X too")
4. **Per-unit walkthroughs** — one per branch/module: overview → file-by-file before/after → subtleties → tests
5. **End-to-end flows** — sequence diagrams that tie the units together
6. **Scope boundaries** — what this change deliberately does NOT do, and where that lives
7. **Reviewer checklist** — invariants, who enforces them, what would break them; questions to ask
8. **Glossary + appendix** — every domain term; the road-not-taken; full listings of anything condensed earlier

### Phase 4 — Author (fragments + components)

Write every fragment to the [prose rules](#prose-rules). Write the document as fragment files, then concatenate in order. This keeps a 1500-line file editable and lets you fix one section without rewriting all of it. Copy [references/template-shell.html](references/template-shell.html) — it contains the full CSS theme and the JS for every component below, with `<!-- @SLOT -->` markers showing where content goes.

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
4. **Read-through** as the reader, top to bottom, against the [prose rules](#prose-rules):
   - the first paragraph of each section states its point
   - no sentence uses a term before the document defines it
   - each before/after says why
   - a short script flags prose sentences over 25 words (text of `p`, `li`, `.wstep`, `summary`, and captions; skip `pre` and `code`). Split each one into shorter sentences; do not cut a fact.
5. Fix and re-check until clean. Delete screenshots and kill the server when done.

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
