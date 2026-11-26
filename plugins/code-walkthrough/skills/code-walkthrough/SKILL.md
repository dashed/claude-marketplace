---
name: code-walkthrough
description: "Create a self-contained interactive HTML explainer that teaches code to a reader with no prior knowledge: a change (branch, PR, diff) or how existing code works (a subsystem, feature, mechanism, or flow), with before/after code toggles, mermaid diagrams, step-through code walkers, and playground widgets, checked in a real browser. Use when the user asks for an explainer HTML file, page, or document, or to explain code as an HTML page; asks for a walkthrough, teaching, or review document of a branch or PR; wants to learn or review a change interactively, or wants before/after explanations with visuals; wants to learn a codebase area from zero; wants a flowchart or statechart of a PR or subsystem in a page, with its rules checked by TLC; or mentions interactive HTML docs or mermaid walkthroughs. Use it instead of show-me or a hand-written page whenever the request is an explainer file."
license: MIT
---

# Code Walkthrough

Produce ONE self-contained interactive HTML file that teaches code from zero prior knowledge: a change, or how existing code works. After a change explainer, the reader can review the change line by line: what each module does, why the seams are where they are, what the failure modes are, and what to scrutinize. After a code explainer, the reader can change the code safely: what each part does, how a request moves through the parts, and which invariants a change must keep.

The output is a teaching document, not a diff dump. Code is quoted verbatim; understanding is built in layers; interactivity does real pedagogical work (toggles for before/after, walkers for execution order, playgrounds for logic under study).

**Aim for understanding over economy.** Put the bottom line first, and write in ASD-STE100. The [prose rules](#prose-rules) give the details.

## When to Use

- "Make an explainer HTML file for this PR" or "an explainer of how the retry scheduler works"
- "Walk me through this branch/PR/diff (before/after) in an HTML file"
- "I want to learn/review this change effectively — make it interactive, with diagrams"
- "Teach me this subsystem from zero" (with code as the source of truth)
- "Show me a flowchart and a statechart for this PR, add them to the explainer, and walk me through them": an explainer with a [state model](references/state-models.md)

Use this skill for every request for an explainer HTML file, also when another skill could write a page (`show-me` writes one focused visual; this skill writes the explainer). The [related skills](#related-skills) do parts of the pipeline.

### Two kinds of explainer

Decide the kind from the request. "An explainer for this PR" is a change explainer. "An explainer of how X works" is a code explainer. Both use the same pipeline, template, prose rules, and browser checks. Only these parts differ:

| | Change explainer | Code explainer |
|---|---|---|
| Subject | a branch, PR, diff, or commit range | existing code: a subsystem, feature, mechanism, or flow |
| Refs (Phase 0) | before and after | the one commit that you read |
| 30-second version | what changes, why, and what the reviewer must check | what the code does, why it has this shape, and what a change must keep |
| Units (Phase 3, step 4) | one for each branch or module, with before/after toggles; a file that the change adds also gets a [file tour](#file-tours) | one for each component, in the order that a request reaches it; a toggle only compares with an earlier design or an alternative |
| Last section before the glossary (Phase 3, step 8) | reviewer checklist | "Before you change it": each invariant, the code that enforces it, and the test that guards it |

If the topic is not code in the repository (a protocol, or the design of a library), use the same pipeline. Take the facts from the source that the user names (a spec, the library's code, its documentation), and cite that source where the document would cite a ref.

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

- **Document.** The "30-second version" comes immediately after the hero. It states what changes, why, and what the reviewer must check (a code explainer states the items in [its row of the table](#two-kinds-of-explainer)). A reader who stops there has the answer.
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

1. Pin the exact refs that define **before** and **after** (branch tips, PR base/head, commit range). For a code explainer, pin the one commit that you read. Write them into the document later — every code claim must trace to a ref.
   - For a GitHub PR, read its facts with `gh pr view <n> --json number,url,headRefOid,baseRefName,files`. Pin **after** to `headRefOid`; `git fetch <remote> pull/<n>/head` gets it, also for a PR from a fork. Pin **before** to `git merge-base <remote>/<baseRefName> <headRefOid>`. The PR's Files changed view compares with the merge base, so the Before line numbers then match its left side.
   - Do not pin a local tip that GitHub does not have. The [source links](#phase-4--author-fragments--components) would open different code, or a 404.
2. Define the audience contract: "no prior knowledge" means no knowledge of *this domain and this codebase* — include a glossary of domain terms, but do not teach the programming language.
3. Identify the 1–3 **core mechanisms** the change builds on (pre-existing patterns the reader must understand first). These get their own foundations sections before any diff is shown.
4. Decide whether the subject has a **state model**: a status or phase that the code changes, a lifecycle, a protocol, a lock or a queue, work that two actors do at the same time, or work that a signal or a crash can interrupt. If it has one, or the user asks for a statechart or a flowchart, plan Phase 2b and the state-model sections, and read [references/state-models.md](references/state-models.md).

### Phase 1 — Extract (fan out, read-only)

Extraction parallelizes well; use subagents for independent units (one per branch/module/ring of context). Rules for every extractor:

- **Read-only**: use `git show <ref>:<path>` / `git diff <a>..<b>` / `git grep <pat> <ref>`. Never check out branches, never modify files, never run the repo's test suite (respect host-repo constraints — e.g. shared test databases, single-runner rules).
- **Verbatim-first**: demand full function bodies, complete diffs, full commit bodies — "do not paraphrase code". Line anchors (`file.py:123`) for every claim.
- Ask each agent for: commit list with bodies, diff stat, per-file verbatim diffs, full tip content of key regions, the "before" state of the same regions, test inventory with the load-bearing tests quoted, and the subtleties *with evidence*.

### Phase 2 — Verify (the phase that makes the doc trustworthy)

Never bake agent output into the document unverified. Independently re-read every critical block yourself at the exact refs: the star functions, the before/after of the core change, anything surprising. Agent reports are leads, not facts — expect a couple of wrong or stale claims per batch and catch them here. If the doc will state a number (test counts, line counts, rows that the code selects), count it yourself. When the count comes from a query, check that the query's filter is the same predicate as the code's. A filter with one of the code's two conditions can count four times the rows that the code selects.

### Phase 2b — Model (when the subject has states)

Load the `statechart` skill. Model the code with the rules that the reader cares about, and check the model with TLC: before and after for a change explainer, the code as it is for a code explainer. Replay each bug path against the real code, and label it reproduced or model only. Model each proposed fix, each alternative, and each simpler design, and check each with the same rules. A claim that a fix or a design works needs the report of its run. [references/state-models.md](references/state-models.md) gives the steps.

### Phase 3 — Structure (spiral pedagogy)

Order the document so each section only needs what came before:

1. **Hero** — title, scope chips (refs, sizes, commit counts); for a PR, the first chip links to the PR
2. **The 30-second version** — the bottom line: what changes, why, and what the reviewer must check, in plain words, with a map diagram
3. **Foundations** — domain 101, the wire contracts/interfaces, the core mechanisms (this is where "the X stuff" gets taught when the user asks "teach me X too")
4. **Per-unit walkthroughs** — one per branch/module: overview → file-by-file before/after → subtleties → tests. A file that the change adds has no "before", so give it a [file tour](#file-tours) before the sections that explain its mechanisms.
5. **End-to-end flows** — sequence diagrams that tie the units together
6. **Flow and states** (when the subject has a state model) — the flowchart and the statechart, how to read the statechart, a walk through one normal run, a rule card for each rule that breaks (its path, why, how likely, and fixes with alternatives), and simpler designs; [references/state-models.md](references/state-models.md#the-sections) gives the order. The 30-second version names each broken rule.
7. **Scope boundaries** — what this change deliberately does NOT do, and where that lives
8. **Reviewer checklist** — invariants, who enforces them, what would break them; questions to ask
9. **Glossary + appendix** — every domain term; the road-not-taken; full listings of anything condensed earlier

A code explainer keeps this order, with the changes in [Two kinds of explainer](#two-kinds-of-explainer).

#### File tours

Sections that explain a mechanism quote only the slice of code that they need, so no section reads a new file in order. A reviewer needs that read. For each file that the change adds:

- Read the file from its first line to its last line, in file order. Every line appears in exactly one quoted chunk.
- A chunk is one function or one coherent block, quoted in full, with line numbers. Put imports and a long module or class docstring in a closed `<details>`.
- Under each chunk, write a line-keyed note list (`.lbl`): each note names the lines it explains and links to the mechanism section that teaches them in depth.
- For each test file, list every test: one table for each test group, with the test's line range, what it sets up, and what it checks. Generate the names and line ranges from the file with a short script, so that they cannot drift; write only the "sets up" and "checks" text by hand.

Keep the mechanism sections. The tour is the linear read, and it links into them. When the mechanism sections are long, the tour can be its own page in a series (see [Scaling notes](#scaling-notes)).

### Phase 4 — Author (fragments + components)

Write every fragment to the [prose rules](#prose-rules). Write the document as fragment files, then concatenate in order. This keeps a 1500-line file editable and lets you fix one section without rewriting all of it. Copy [references/template-shell.html](references/template-shell.html) — it contains the full CSS theme and the JS for every component below, with `<!-- @SLOT -->` markers showing where content goes.

**Component library** (all wired in the template; use them, don't reinvent):

| Component | Use for |
|---|---|
| Sidebar TOC + scrollspy | navigation in long docs |
| Before/after tab toggles | every meaningful diff — reader flips between base and tip |
| Diff-colored lines (`.cl.add/.cl.del/.cl.hl`) | real diffs (add/del) and attention (hl = not a diff!) |
| Line numbers (on by default) | every quoted block: `data-start` on the `<code>`, a `.cl.gap` line for each elision, `data-old-start`/`data-new-start` for a unified diff |
| Line-keyed note list (`.lbl`) | the notes under each chunk of a [file tour](#file-tours) |
| Source links (when the code is on GitHub) | the `#walkthrough-source` block (repository, PR, base and head SHAs, the PR's files) and `data-path` on each quoted block; the JS links each block's line range at the pinned commit and in the PR's Files changed view, and each `.ln` range |
| Syntax highlighting (`<code class="language-python">`) | every code block — highlight.js colours the tokens and keeps the per-line diff/walker classes |
| Collapsible `<details>` deep-dives | side context that would interrupt the spiral |
| Step-through walker | execution-ordered code (a write path, a state machine) — steps highlight line ranges |
| Mermaid diagrams | chain maps, ER diagrams, dependency graphs, sequence diagrams, state transitions |
| Callouts (`.note/.warn/.key`) | the one idea per section the reader must not miss |
| Glossary-linked `<dfn>` | domain terms, clickable to the glossary |
| Light/dark theme | follows the OS until the reader toggles (then persisted); set before first paint; code tokens and diagrams re-theme too |
| Playground widgets | mirror the logic under study in JS (a validator the reader can throw inputs at, a scheduler that shows race outcomes) — the strongest teaching tool when the domain allows |
| Statechart (`.mermaid[data-statechart]`) | a `chart.mmd` from the statechart command, pasted verbatim; its marks (`breaks`, `mayBreak`, `bugPath`, `repeats`) and group colours follow the theme |
| Chart walker (`data-chartwalk`) | a walk through a statechart: one normal run, then each bug path in the report's numbering; each step highlights its state and scrolls it into view |
| Rule card (`.rulecard`) and chips (`.chip`) | one card for each rule that breaks: the rule, its path, why, how likely, and a toggle of fixes, each with its TLC verdict |
| Design comparison | a before/after toggle of statecharts, one for each design, each with its numbers from the report |

**Fidelity rules:**

- Quote code **verbatim** at stated refs. If you condense, mark it ("condensed for width", elision comments) — never silently alter.
- HTML-escape everything (`<=` → `&lt;=`); run the balance check in phase 5 to catch what you missed.
- `add`/`del` colors only for lines that are actually added/removed in the diff; use `hl` for emphasis elsewhere.
- Number every quoted block with the file's own line numbers at the stated ref. Number a Before pane from the old file and an After pane from the new file. In a unified diff, a removed line shows its old number and every other line its new number; read both start numbers from the hunk header (`@@ -a,b +c,d @@`). An elision line gets no number.
- Do not write line numbers in prose ("the check at lines 111-112"). They go stale when the change moves, and nothing remaps them. Name the function, or link to the quoted chunk. The `.lbl` notes are the exception: they sit under the chunk that they number.
- When the subject is a GitHub PR, every quoted block links to its lines on GitHub, and the hero links to the PR. Fill the `#walkthrough-source` block once. Put `data-path` on every quoted block, and `data-ref="base"` on each Before pane. The JS builds each link from the block's line numbers, so the link always covers the lines that the block shows. Do not write these URLs by hand. Use the same block for a code explainer of code on GitHub, without `pr`, `files` and `base`.
- A block quoted from another repository (a library, a spec) gets no `data-path`. Link its source in the caption.
- Put `language-<name>` (a highlight.js name or alias: `python`, `ts`, `tsx`, `go`, `sql`, ...) on every code block's `<code>`. Keep lines plain text — no `+`/`-` prefixes, no spans inside a `.cl` line; a line with markup in it opts its whole block out of highlighting.
- No hard-coded colours in mermaid source (`style X fill:#…`, coloured `classDef`): they break in one of the two themes. Mark the node the reader should look at with `class NodeId current`.
- Paste each `chart.mmd` into a `.mermaid[data-statechart]` unchanged; never draw or edit a statechart by hand. Its `classDef` colours do not break the colour rule above: the template drops them. A bug path uses the report's numbering and words. A `breaks` or `holds` chip needs a report in the fragments folder, and a `reproduced` chip names the test or the command. A TLA+ block uses `language-plaintext`, because highlight.js has no TLA+ grammar.
- Validate each diagram's source with the `mermaid-cli` skill before it goes into a fragment: `mmdc -i diagram.mmd -o diagram.svg` exits 1 and prints the parse error with its line. In the page, a syntax error shows only as an error graphic.
- No planning artifacts, ticket IDs, or local scratch paths in the document unless the user asks for them.

### Phase 5 — Verify in a real browser

1. **Structure**: parse the HTML (any lenient parser) for unbalanced tags; check every `href="#…"` resolves; check tab buttons match panes; count mermaid blocks.
   - **Line numbers**: every quoted block has `data-start` (or the diff pair), and every `.cl` line that is not a `.gap` has a `data-n` after load.
   - **File-tour coverage**: for each added file, the tour's chunks cover lines 1 to the file's last line at the pinned ref, with no gap and no overlap. Compare the first and last `data-n` of each chunk with `git show <ref>:<path> | wc -l`.
   - **Quoted ranges start where they claim**: print the first line of each quoted function or test. It must be its `def`, its `class`, or its first decorator. A range that starts on another test's decorator is a wrong range.
   - **Prose line numbers**: search the text outside `pre`, `code` and `.lbl` for `lines? \d+`. Each hit is a number that the next re-pin will leave stale.
   - **State models** (when the page has one): the checks at the end of [references/state-models.md](references/state-models.md#phase-5-checks).
   - **Source links** (when the page has the source block):
     - The hero links to the PR, and every quoted block from the repository has `data-path`.
     - `gh pr view <n> --json headRefOid` still equals the pinned head. If the PR moved, re-pin.
     - Dump each numbered line from the page as (path, commit, number, text), and compare it with `git show <sha>:<path>`. The commit is the base for a `data-ref="base"` block and for a removed line in a unified diff, and the head for all other lines. A link is correct only when the quoted text is on the lines that it opens. Each difference must be a marked condensation.
2. **Render**: serve the file on a free port (`python3 -m http.server 0 --bind 127.0.0.1`, then read the port; a fixed port can hit a stale server and check its 404 page) and drive a headless browser (the Playwright MCP tools, or the `playwright`, `dev-browser`, or `chrome-cdp` skill):
   - every `.mermaid` contains an `svg` (count them), and no `svg` has `aria-roledescription="error"`. Mermaid draws a syntax error as an SVG that reads "Syntax error in text", so the count alone passes a broken diagram. `mmdc` runs its own mermaid version, and the template loads mermaid 10.9.3, so newer syntax can pass `mmdc` and still fail here.
   - every `code[class*=language-]` block contains `.hljs-*` spans and still has its original number of `.cl` lines
   - walker: click next/prev, assert the active step and highlighted lines change, and that the first highlighted line is inside the code pane. Read the expected lines from the step's `data-lines`, not from a hard-coded number, so that a re-pin does not break the check
   - chart walker: at each step, exactly one state has `cw-on`, it is the state that `data-node` names, and it is inside the chart pane
   - tabs: toggle each group, assert pane visibility flips. Skip the groups inside a closed `<details>`: they are not clickable until it opens
   - source links: each block's `L<a>-L<b>` link matches its first and last `data-n`, and a block whose file is in `files` also has a `PR #<n>` link. Open one link of each kind and look at the highlighted lines
   - phone width (390 px): the page has no horizontal scroll (`scrollWidth` equals `clientWidth`), and each walker's "next" button is inside its card
   - theme: toggle dark, assert the diagram SVGs were replaced (new `svg` ids) and re-check readability of diagrams and code
   - playgrounds: exercise them via `evaluate` (set input, assert verdict output)
   - console: no errors (a favicon 404 is fine; a 404 for `…/languages/<name>.min.js` means a `language-` name highlight.js does not know)
3. **Screenshots** in light AND dark of the hero, one diagram-heavy section, and each custom widget — look at them yourself; rendering bugs hide in screenshots, not in DOM assertions. Take element screenshots (`locator.screenshot()`): a page screenshot clipped to coordinates fails for an element below the fold.
4. **Read-through** as the reader, top to bottom, against the [prose rules](#prose-rules):
   - the first paragraph of each section states its point
   - no sentence uses a term before the document defines it
   - each before/after says why
   - a short script flags prose sentences over 25 words (text of `p`, `li`, `.wstep`, `summary`, and captions; skip `pre` and `code`). Split each one into shorter sentences; do not cut a fact.
5. Fix and re-check until clean. Delete screenshots and kill the server when done.

### Phase 6 — Deliver

Deliver the single HTML file at the requested path. The deliverable is the local file; publish it as an Artifact only when the user asks for a link. Once the user has asked for a link, publish again to the same URL after each rebuild that passes Phase 5. Keep the fragments directory (mention it — it is how the user iterates). Note the two external dependencies (mermaid and highlight.js, both from the jsDelivr CDN) and that offline the document degrades to plain code and readable diagram source. If the user is currently reading an earlier document, write a NEW file and cross-link; never edit a file the user has open.

## Related skills

Load each one at the phase that needs it:

| Skill | Phase | Job |
|---|---|---|
| `mermaid-cli` | 4 | Validate each diagram's source with `mmdc` before it goes into a fragment. |
| `statechart` | 2b, 4 | Check a TLA+ model of the code's states with TLC, and write the `chart.mmd` and `report.md` that the state-model sections show. |
| Playwright MCP tools, `playwright`, `dev-browser`, or `chrome-cdp` | 5 | Serve the page, run the render checks, and take the light and dark screenshots. |
| `dataviz`, when it is available | 4 | Draw a chart (numbers over time or across categories) as inline SVG that uses the page's colour variables, so it follows the theme. |
| `show-me` | — | A quick visual in the chat or one focused page. It sends a request for an explainer file to this skill. |

## Pitfalls (learned the hard way)

1. **Mermaid + dynamic import**: `mermaid.initialize({startOnLoad: true})` silently never renders when the import resolves after the load event. Use `startOnLoad: false` + explicit `await mermaid.run({querySelector: ".mermaid"})`, with a fallback that swaps diagrams for their (readable) source text if the CDN is unreachable.
2. **Dark-mode diagrams**: mermaid's stock themes are fixed palettes; the neutral theme draws dark text, invisible on a dark page. The template uses the `base` theme with `themeVariables` read from the page's CSS colours, and re-renders every diagram when the theme changes. It renders off-screen and swaps the SVG in, because rendering in place shows raw source mid-render, and a diagram inside a hidden tab or closed `<details>` lays out broken (clipped notes, missing actor boxes).
3. **Highlighters flatten line markup**: `hljs.highlightElement` and similar re-read `textContent` and replace the block, destroying the `.cl` line spans that carry diff colours and walker line numbers. The template highlights the joined text and splits the HTML back onto the lines, closing and re-opening any span (a multi-line string or comment) that crosses a newline.
4. **Empty grep false negatives**: an empty result from a tree-wide search proves nothing if you were in the wrong directory. Sanity-grep a term you KNOW exists first; check `pwd` after hopping between repos.
5. **Agent claims ≠ facts**: the two classic failures are plausible-but-wrong mechanism descriptions ("the setting lives in an org option" — actually a model column) and unverified counts ("12 tests" — actually 7). Phase 2 exists for this; do not skip it when the agents sounded confident.
6. **`order_by` vs in-Python sort** (and similar framework subtleties): when the code comments explain a non-obvious choice, quote the comment — it is usually the reason the reader was confused.
7. **cwd drift**: assembling fragments or running validation from the wrong working directory produces confusing "file not found" storms. Use absolute paths in assembly commands.
8. **Re-pinning by line map**: when the PR moves, a `difflib` line map from the old file to the new one is wrong for a range that starts on a line that repeats, such as the decorator above every test: the range moves onto another test. Find each quoted function or test again by its name in the new file, then run the "quoted ranges start where they claim" check.
9. **Chained replacements**: remapping numbers one pair at a time turns `243 → 245` and then the new `245 → 247`. Remap in one pass with a lookup table.

## Scaling notes

- Small change (≤3 files): skip agent fan-out; extract directly, still follow phases 2→5.
- Multi-branch stacks: one document per 1–2 branches, cross-linked in a series — better than one 4000-line document. Give each part a chain-map diagram with the current part highlighted (`class NodeId current`).
- Keep widgets honest: a playground must implement the same logic as the code it teaches (port the checks, don't fake outcomes), and say so in the document.
- One owning page for each topic. In a series, other pages summarize a topic in a few lines and link to its page. They do not keep a second copy of its walkthrough: the copy goes stale, and the reader cannot tell which page is right.
- A change that moves often (fix commits, a rebase, review rounds) makes the re-pin the most expensive step. Keep every SHA (base, head, each commit) in one table, which also fills the `#walkthrough-source` block, and every number that the prose states in one list of facts named by meaning, and fill them in when the fragments are assembled. Give two quantities two names even when they are equal today: a later commit can change one and not the other. Let a widget read its "decided at" line numbers from the same assembly step, not from constants in its JS.
