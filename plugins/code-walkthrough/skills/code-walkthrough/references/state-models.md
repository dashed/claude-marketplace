# State models in an explainer

When the code moves between states, the explainer shows two diagrams: a flowchart of one run, and a statechart that TLC checks against the rules that the reader cares about. It teaches the reader to read the statechart, walks them through it, explains each rule that breaks with fixes and alternatives, and proposes simpler designs. This file is the procedure. `SKILL.md` places it in the pipeline (Phase 0, Phase 2b, Phase 3, Phase 5).

## Contents

- [When the subject has a state model](#when-the-subject-has-a-state-model)
- [Two diagrams, two jobs](#two-diagrams-two-jobs)
- [Phase 2b: build and check the model](#phase-2b-build-and-check-the-model)
- [Fixes and alternatives](#fixes-and-alternatives)
- [Simpler designs](#simpler-designs)
- [The sections](#the-sections)
- [Rule cards: make a break easy to understand](#rule-cards-make-a-break-easy-to-understand)
- [Phase 5 checks](#phase-5-checks)

## When the subject has a state model

Add the model when the code has one of these:

- a status field, a phase, or an enum that the code changes
- a lifecycle: start, run, retry, time out, stop, clean up
- a protocol between two parties, or a workflow with approvals
- a lock, a lease, a queue, or a cache with invalidation
- work that two processes, workers, or requests can do at the same time
- work that a signal, a timeout, or a crash can interrupt

Also add it when the user asks for a statechart, a state diagram, a flowchart, or a TLA+ check. A pure transform of data has no states: give it a flowchart at most.

## Two diagrams, two jobs

- **Flowchart**: the order in which the code runs for one request. Draw it by hand from the code, as a mermaid `flowchart`. Each node is a function or a branch. Under the chart, a line-keyed note list (`.lbl`) maps each node to its code.
- **Statechart**: every state that the model reaches, and every step between them. It includes the steps that come from outside the code path: a second user, a crash, a signal, a timeout. A flowchart does not show these, and most bugs start there. TLC draws the statechart through the `statechart` skill. Never draw a statechart by hand.

Say this difference in one paragraph before the two charts.

## Phase 2b: build and check the model

Load the `statechart` skill and follow its `SKILL.md` for the spec, the config, the view, and the report. Then:

1. **Extract**, with the file and function for each item:
   - variables: what the code stores or what the reader can see (a status column, a phase, a flag, a file that exists), plus a writer list naming every code path that writes each variable (mapped to an action or explained as omitted)
   - actions: each code path that changes a variable, and each event from outside; for each restricting guard conjunct, cite the enforcing check or early return across every entry point, leave the action permissive if unverified, or isolate it as an `Assume_*` operator
   - rules: what must always be true, or must happen in the end, in the reader's words. Take them from the PR description, the tests, the docs, the code comments, and the reviewer checklist. When a rule is your inference, the page says so.
2. **Map each action to its code** in a table (action, file, function). The walker steps and the rule cards link each step to its code from this table.
3. **Model only what the rules need.** Use small values: one request, two workers, a counter that stops at 3. Keep the model under the chart budget of 500 states, and the chart near 20 arrows.
4. **For a change explainer, model before and after** with the same rules and the same view. Read the changed code directly rather than patching only the before-spec, and re-audit every guard on and every writer of any variable that the change newly reads. The two reports show what the change fixes and what it breaks.
5. **Run the statechart command** in a scratch folder outside the repository. Keep the spec, the config, `view.py`, `report.md`, `chart.mmd`, and each `tlc-RULE.out` in the fragments folder under `model/`.
6. **Replay each bug path and probe assumptions against the real code**, as the statechart skill says: a test or a live repro, one step for each action. Also run a refusal probe for every `Assume_*` guard that `report.md` lists under `## Assumptions` as relied on by a holding rule; if the code allows the excluded action, drop the guard and rerun. Work in a scratch copy or a throwaway worktree. Do not run the repository's own test suite, or touch a shared service, without the user's approval (the Phase 1 rule). Keep the command and its output.
   - **reproduced**: the path ran on the real code and the rule broke. The page names the test or the command.
   - **model only**: the path did not run, or it did not break the rule. Until a replay shows otherwise, think that the model is wrong. Fix the model, or say in the page why the path did not run.
7. **The page is the hand-off.** Do not post findings to the PR.

## Fixes and alternatives

For each rule that breaks:

- **Proposed fix**: the smallest change that makes the rule hold and breaks no other rule.
- **One or two alternatives** that differ in kind: a different owner, a different order, a different mechanism. Two variants of one idea are one alternative. Describe the alternative that you reject as fully as the fix that you propose.
- **Model each one.** Read the proposed change and re-audit every guard on and every writer of any variable the fix newly reads before running the check with the same rules. Record the verdict for each fix: "every rule holds", or the rule that still breaks. Never write that a fix works without the report of its run.
- **For each one, say**: the code that changes (a sketch, marked as a proposal, never shown as quoted code), what it costs (lines, a new process or thread, behavior that changes, a window that it leaves open), and the other breaks that it also fixes.
- **Recommend one**, and say why.

## Simpler designs

After the fixes, read the model and the chart for a design with less to go wrong:

- Two variables that must agree, such as a flag and a phase: keep one.
- States that the reader cannot tell apart (the same label and the same steps out): merge them.
- A step that only recovers from a state that a different order avoids: change the order, so that the safe state comes first.
- Two actors that clean up the same thing: give it one owner.
- A window between two steps that must happen together: make them one step, or make the first step safe alone.
- A rule that holds only because of timing: remove the timing assumption.

For each proposal, model it as a design of its own ("Design B"), and check it with the same rules. Compare its numbers from `report.md` (states, steps, chart states, arrows, the rules that hold) with the current design's. Say what the code change is and what it costs. Propose only a design that keeps each rule that the current design keeps, or say which rule it gives up and why that is acceptable.

## The sections

Place these after "End-to-end flows" and before "Scope boundaries":

1. **Flow and states**: the flowchart, then the statechart, with the paragraph on their two jobs.
2. **How to read the statechart**: one short list that uses this chart's own states and legend. A box is a state, named in the reader's words. An arrow is a step, named by what happens; text in brackets is the condition for the step. `[*]` marks where a run starts. A box inside a box is a state with parts. "At the same time" holds regions that change on their own. Then each mark: red (`breaks`), the state always breaks a rule; orange (`mayBreak`), only some model states behind it break it; blue border (`bugPath`), the state is on a shortest path to a bug; dashed purple border (`repeats`), a run can stay here forever, which breaks a rule about what must happen in the end. Also say what the chart does not draw: steps that stay in one state, and the steps that the view hides (name them).
3. **A walk through one normal run**: a chart walker over a run that keeps every rule, from the start to an end state.
4. **Rules**: a table with one row for each rule (the rule in the reader's words, TLC's verdict, reproduced or model only — plus any unprobed `Assume_*` guards or omitted writers beside `holds` verdicts). Then one rule card for each rule that breaks, in order of impact.
5. **Simpler designs**: a design comparison, with the recommendation.

The 30-second version names each broken rule in one sentence, with its impact (bottom line up front). The reviewer checklist, or "Before you change it" in a code explainer, lists each rule and the code that keeps it.

## Rule cards: make a break easy to understand

A rule card (template pattern 12) has these parts, in this order:

1. **The rule** in one sentence of the reader's words, then its TLA+ line. Use `language-plaintext`: highlight.js has no TLA+ grammar.
2. **What breaks it.** Start with the story: a concrete run in plain words, such as "You pipe the output into `head`. The check passes, and the command still exits 2." Then a chart walker over the shortest path, in the report's numbering and words (`0. state`, then `1. step: state`). Each walker step names the code that takes the step, and links to it.
3. **Why.** The one step where the rule fails, and what the code assumed there.
4. **How likely, and what it costs.** When it happens, with a measured number when you have one (a window in milliseconds, a rate, a size), and what the reader loses.
5. **Fixes.** A toggle with one pane for each fix. Each pane has its TLC verdict chip, the sketch, and the costs. The recommendation comes last.

The chips: `breaks` or `holds` from the report, and `reproduced` or `model only` from the replay.

## Phase 5 checks

- The text of each `.mermaid[data-statechart]` equals its `chart.mmd` byte for byte (after HTML unescape).
- Each statechart renders with no error graphic. The SVG's own style has no `.breaks>*` or `.mayBreak>*` rule (the template dropped the chart's `classDef` lines).
- Each chart walker step's `data-node` is a state in its chart (`g[id^="state-<id>-"]`). Step through each walker, in both themes and at 390 px: the current state is inside the chart pane at every step.
- Each path in a rule card matches `report.md`: the same numbering, the same step labels, the same states.
- Each verdict chip has its report in `model/`. Each `reproduced` chip names a test or a command whose output is kept.
- The page names every hidden step that the report counts ("The view hides N steps").
