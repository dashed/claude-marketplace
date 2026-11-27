---
name: statechart
description: "Check a TLA+ model of a system that moves between states, such as a product flow, a protocol, or a service, with the TLC model checker, and draw it as a Mermaid statechart in the words of the person who must decide whether the behavior is right. The report gives the shortest path to each state that breaks a rule. Use when the user runs /statechart, asks to model-check a state machine, flow, or protocol with TLA+ or TLC, wants a statechart that marks the states where a rule breaks, or wants a bug shown as a path through states. Not for a Mermaid diagram that needs no model check (mermaid-cli, show-me) or for an explainer HTML file (code-walkthrough)."
---

# Statechart

The chart shows how a system moves between states, in the words of the person who reads it. That person, the reader, decides whether the behavior is right.

## Run

Work in a scratch folder outside the repo. Write a TLA+ spec and its config. Then run:

```sh
uv run --no-config --quiet --script <skill dir>/scripts/statechart.py SPEC.tla [--config FILE] [--view FILE] [--out DIR]
```

`scripts/statechart.py` is a Python 3.10 script with no dependencies, and uv finds or installs a Python for it. On macOS and Linux, `<skill dir>/scripts/statechart` runs the same command.

The first run installs TLC and Java with mise and needs the network. Without mise, set `TLA2TOOLS` to the path of `tla2tools.jar` and `JAVA` to a Java 11 or later binary.

## Write the spec

- Write each rule that the reader agrees to as an INVARIANT. A rule can be about a screen, a result, a stored value, or a message. If the model has no variable for a rule, add the variable. Never weaken a rule to make it hold.
- When a rule says that something must happen in the end, such as "TLC stops after the command dies", write it as a PROPERTY with `~>`, such as `Gone ~> check # "running"`. As an INVARIANT it breaks in each state between the event and the step that answers it. Define `Spec == Init /\ [][Next]_vars /\ WF_vars(Cleanup)` with `WF_vars` for each step that must happen when it can, and give `SPECIFICATION Spec` in the config. The report then gives TLC's counterexample, which ends in the states that repeat forever.
- Write `Next` as a disjunction of the actions, such as `YouPressPlay \/ YouPressStop`. If you do not, TLC names every step `Next`.
- A state with no step out breaks `NoDeadlock`, also when it is a correct end state. When an INVARIANT or a PROPERTY already has that name, the rule is `CHECK_DEADLOCK`. Add to `Next` an action that is true only in the end states and changes nothing, such as `Done == phase \in {"paid", "failed"} /\ UNCHANGED vars`, and give it a label in `step()`.
- Model one layer per spec rather than one large model that mixes a protocol, a domain lifecycle, and I/O details. Keep only the variables that the rules need, and use small constants. If the model still grows past the 500-state chart budget, split it into an abstract spec (such as resource conservation or ownership) and a separate spec for the detailed lifecycle instead of weakening the rules.

## Pick the chart

You do the work that needs judgment: the words on each state and arrow, the phases and their colors, the title, and the report to the reader. Put your work in a Python view module, such as `view.py`, and give it with `--view`.

To show the reader's words, the view defines `state(vars)`. The value that `state()` returns picks the form:

- A string gives a flat chart: `def state(v): return "The card is charged" if v["paid"] else "You are paying, and the card is not charged yet"`
- A list gives parent states: `def state(v): return v["main"].split(".")`
- A dict gives one parallel region for each key: `def state(v): return {"Playback": v["playback"], "Volume": v["volume"]}`

`vars` is the state as JSON: a record, a sequence, or a function is a dict with string keys, so `v["pc"]["1"]` is `pc[1]`, and a set is a list. Write each label as "Write the labels" says.

The view can also define `step(action, from_, to)`. It gets the TLC action name and the values before and after the step, and it returns the label of the arrow. The steps between the same two chart states, with the same condition, share one arrow, and the command joins their labels with "or". Give two actions the same label when the reader does not need to tell them apart.

When a step can occur only in some conditions, end its label with the condition in brackets, in the reader's words, such as `you press play [while the file loads]`. In a regions chart, the command writes the condition on the other regions on the arrow, in the words of their labels, such as `[when Offline]`. Your brackets replace it, and two arrows from one state can then look the same. So in a regions chart, do not write brackets for a condition on another region. When a value that no label shows decides where a step goes, name the result in the label, such as "the roster read fails".

The view can also define these:

- `group(vars)` returns the name of a phase. Each chart state gets the color of its group. When the model states behind one chart state are in different groups, that state gets no color.
- `colors` is a dict that gives each group name a color class.
- `title` is a string that the chart shows at the top.

Start any other name in the view with `_`, such as `_LABELS`, or list the five names in `__all__`. The command refuses a view that defines a name it does not read. Imports do not count.

The command calls `state()` and `group()` at most once for each model state, and `step()` at most once for each step. The chart and the report both use those answers. So make each function depend only on its arguments.

The chart does not draw a step that stays in one label. Split a label when the reader must see such a step.

Aim for about 20 arrows or fewer, because a busier chart is hard to read. First return fewer states from `state()`. Give one label to values that act the same, and leave out a detail that the reader does not need, such as a call in flight whose return changes nothing. Keep each state of a bug path, and keep each mark. When a merge changes a `breaks` state to `mayBreak`, it hides where a rule breaks. Do not merge two states that break different rules, because the reader then cannot see which rule breaks where. When one step goes from many states to the same state, such as a crash that can happen at any time, put those states under one parent: `state()` returns a list such as `["The command is alive", "The command waits for TLC to finish"]`, and when each state under the parent takes the step, the command draws it once, from the parent. Do not shorten labels to make a chart less busy: a short label removes no state and no arrow. If the chart is still too busy, return `None` from `step()` for the steps that the reader does not need, such as a reset that every state has, or a step whose arrow repeats what other arrows show. Obey these rules when you hide steps:

- Keep each chart state reachable by arrows from a start state.
- Keep at least one arrow out of each chart state that has a step out in the model.
- Hide all the steps of an arrow, or none of them. When you hide only some, its condition gets narrower.
- In the hand-off, say which steps the chart hides.

## Write the labels

The reader reads the chart, and the paths in the report, without the spec or the code. A label of one or two words, such as "Killed" or "Cleaning up", makes the reader guess what was killed and what is cleaned up. Write each label as a clause of about 4 to 12 words:

- A state label says who does what, or what is true, in that state: "The command waits for TLC to finish", "You are paying, and the card is not charged yet", or "The lease is held, and the write is pending". Name each actor and each thing, such as the command, the janitor, or the card.
- A step label says who does what: "you press play", "the connect fails", or "SIGKILL or a crash ends the command". When the reader needs the result of a step, such as an exit code or a count, add it in parentheses: "TLC failed (exit 2)". Brackets are for conditions.
- Write each step label as one clause with no comma, so that the labels on one arrow still read as one sentence when the command joins them with "or": "TLC exits or the command kills TLC after Ctrl-C".
- Write in a label only what is true in each model state behind it. The marks show where a rule breaks, so do not write a rule as a fact: write "The command is dead, and TLC may still run", not "The command is dead, and TLC has stopped".
- Keep variable names, action names, and code out of labels.

Pele and Mermaid 11 wrap a label at about 200 pixels, so a full label makes a taller box, not a wider chart. Mermaid 10 does not wrap: render with Pele or Mermaid 11, or break the lines before you render, as the code-walkthrough template does. The chart text writes a semicolon as `#59;`, so use a comma.

## Read the report

- In the chart, a state that breaks a rule has the class `breaks`. When only some model states behind it break the rule, it has the class `mayBreak`. The Legend names the rules of each mark. When two rules break, it names both on one mark, so say in the hand-off which state breaks which rule. In a regions chart, a state gets a mark when each combination of region states that includes it can break a rule. When a combination can break a rule and none of its states has a mark, each state in that combination gets a mark.
- TLC goes past a state that breaks a rule, so the chart shows the states after a bug.
- Because TLC goes past bugs, a model with no limit on its states can run without end. Keep the constants small, or add a CONSTRAINT.
- With a VIEW or a SYMMETRY, TLC counts states that it treats as the same as one state, and the chart draws that one state. An arrow can lead to it rather than to the state that the step reaches, and the report says so. Use `SYMMETRY` only when the modeled values are truly interchangeable: an unsound symmetry assumption can hide bugs, and TLC's liveness (`PROPERTY`) checks are unsound under `SYMMETRY` — check `PROPERTY` rules without it.
- TLC checks the rules in each state past a CONSTRAINT or an ACTION_CONSTRAINT, but it does not explore that state or check it for deadlock. When TLC's shortest path for a rule ends in such a state, the chart draws that state, and the report gives that path. The chart does not draw the other states past the bound. A deadlock in such a state does not show. TLC also checks the rules after each step that an ACTION_CONSTRAINT excludes, also when it reaches the next state another way. When TLC's shortest path for a rule ends with such a step, the chart draws that step.
- The command checks the rules with TLC on the config as written, with one worker. When a rule breaks, the command removes that rule and runs TLC again, until no rule breaks. After the first break, each run stops at 100,000 distinct states, so that a large model does not run without end. When a run reaches that bound or stops on an error, the report lists the rules that it did not check under "Rules not checked", and the chart does not mark them. A rule that is not checked can hold or break. To check it, remove the rules that break from the config, or make the model smaller. The bound adds a module that changes TLC's order of the variables, so for a property TLC can find a different counterexample than a run without the bound.
- `tlc.out` is what TLC printed on the config as written. When the chart does not show the bug path of a rule that breaks, `tlc-RULE.out` is what TLC printed for the run that found it. When TLC repeats its first warning, plain TLC prints it twice, but `tlc.out` shows it once, because TLC leaves the second copy out of the output that this command reads. That happens only when Java runs with `-XX:+UseParallelGC`, since otherwise TLC's first warning is its advice to pass that flag, which it prints once.

## Show the chart

Show `chart.mmd` to the user as a `mermaid` code block. The chart has a budget of 500 states, counted by TLC on the config as written. Above that, the chart draws only the paths to the rules that break, and when no rule breaks, the command writes no `chart.mmd`. It still checks each rule, and the report gives the state count and each bug path. To see the whole graph, make the model smaller.

In an explainer page, the code-walkthrough skill embeds `chart.mmd` unchanged, teaches the reader to read it, and walks each bug path; its `references/state-models.md` gives the steps.

Render charts with Pele. When the user asks for an image, or a chart is too large to read as text, follow `references/render.md`. Do not use a different renderer unless the user asks for it.

## Hand off

Give each chart and its Mermaid text to the person who must decide. Add one line for each bug: the rule, the reader's sentence for that rule, and the path as the report numbers it. Say what the model leaves out. Give the command that makes the files again, with a new `--out` folder.

When the model describes code, replay each bug path against the real code, as a test or a live repro, one step for each action. If a bug does not occur, think that the model is wrong until you show that it is not.

A clean run has the opposite trap: every rule holding in the model does not prove the code is bug-free. It holds only for the finite constants and assumptions in the spec, and a rule can pass vacuously if an overly tight guard stops the risky action or state from ever being reached. Before trusting a passing model, check the chart to confirm that the expected states and failure actions actually appear (when a rule passes suspiciously cleanly, temporarily break the design or add a reachability check to verify the risky path is reachable), and state the model's key assumptions (such as atomicity, bounds, or unmodeled failures) in the hand-off.

## Credits

Adapted from the [statechart](https://github.com/cursor/plugins/tree/main/pstack/skills/statechart) skill in Lauren Tan's pstack plugin for Cursor, licensed under MIT (`LICENSE` at the plugin root), at commit `b7b93c36be`. This repository maintains its own version. Its command is Python rather than TypeScript, its views are Python modules, and `step()` hides a step by returning `None`. Its process lifecycle was changed after checking a model of it with this skill ([notes](https://github.com/dashed/claude-marketplace/tree/master/notes/statechart)): the janitor starts before the command makes its folders, the worker stops its own check when the command dies, and a reader of stdout that goes away no longer changes the exit code. It also has "Use when" triggers in place of `disable-model-invocation: true`, and the guidance on rules that must hold in the end, layered models and SYMMETRY, false negatives / vacuous passes, and full labels.
