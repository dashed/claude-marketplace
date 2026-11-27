# statechart

The skill checks a TLA+ model with TLC and draws it as a Mermaid statechart. It came from the statechart skill in Lauren Tan's pstack plugin for Cursor (MIT); this repository maintains its own version.

## The command

`scripts/statechart.py` is Python 3.10 or later with no dependencies, run with `uv run --script`. It began as a TypeScript program, and its output follows that program's rules, which `scripts/js.py` keeps: strings sort by UTF-16 code units, whitespace and `trim()` follow JavaScript, JSON has no spaces, and an object lists its array-index keys first.

Three processes run a check:

- the **command** (`statechart.py`) checks the output folder, starts the others, waits, and moves the finished files into `--out`;
- the **worker** (`worker.py`) runs SANY and TLC and writes the files into a stage folder beside `--out`;
- the **janitor** (`janitor.py`) cleans up when the command dies before it can.

## Tests

`make test-statechart` runs ruff, ty and `tests/test_statechart.py`:

- 33 specs from the original skill's corpus (`tests/fixtures/statechart/corpus`), replayed with no TLC or Java: the fixture `java` prints what TLC printed when the corpus was recorded. Each case checks the chart, the report, the exit code and the configs that the command gives TLC (`runs.log`). With `TLA2TOOLS` set, the same specs also run on real TLC.
- The lifecycle paths below, each replayed against the real command.

When the command was ported to Python, the TypeScript and Python versions gave byte-identical output on the corpus (replayed and with real TLC 1.7.4), on 20,000 random charts, and on 30,000 random values, configs and Mermaid labels.

## The lifecycle model

The skill was used on its own command. `lifecycle/CommandRun.tla` models the lifecycle as first ported to Python: the command, the worker's process group, the janitor, Ctrl-C, a SIGKILL of the command at any point, a reader of stdout that goes away, and a child process that fails to start. Its rules:

- **OutputOnlyOnSuccess** (INVARIANT): an exit of 2 or 130 means the command wrote nothing, as its usage text promises.
- **TLCStopsAfterCommand** (PROPERTY): once the command is gone, TLC stops.
- **FoldersGoAfterCommand** (PROPERTY): once the command is gone, its stage and temp folders go.

The last two are properties, not invariants: each is false for a moment after the command dies, until the janitor acts. `SKILL.md` now says so.

All three broke (`lifecycle/CommandRun-report.md`, `lifecycle/CommandRun-chart.mmd`), and each path reproduced on the real command:

| Path | What happened |
|---|---|
| The reader of stdout goes away (`statechart ... \| head`) | The files were written, then printing failed: exit 120, from Python's failed flush at exit, with "Broken pipe" on stderr. |
| SIGKILL after the stage folder exists, before the worker starts | The stage and temp folders stayed. |
| SIGKILL after the worker starts, before the janitor starts | The worker ran on with nobody to stop it, and its folders stayed. |
| The janitor fails to start | The command exited 2 and left the worker running. |

The window for the two SIGKILL paths was about 4 ms of startup (3.3 to 6.7 ms over 50 runs). Ctrl-C and SIGTERM there were handled.

`lifecycle/CommandRunFixed.tla` is the fix, and every rule holds in it (`lifecycle/CommandRunFixed-report.md`):

- The janitor starts first, before any folder exists. The command picks the folder names, the janitor gets them as arguments, and the command makes the folders after.
- The command tells the janitor `pid N` after it starts the worker, and `exited` when the worker ends.
- The worker's stdin is a pipe from the command. A thread in the worker reads it, and when it closes, the command is gone and the worker kills its own process group. The thread reads the file descriptor: blocking in `sys.stdin.buffer.read()` held stdin's lock, and Python aborted the worker at exit, which the corpus tests caught.
- If the janitor is gone when the command tells it the pid, the command stops the check and exits 2. Cleanup kills a worker that still runs.
- A report that cannot print no longer changes the exit code. The command points stdout at the null device, so Python's flush at exit cannot fail either.

`tests/test_statechart.py` replays each path: SIGKILL before and after the worker starts (`tests/fixtures/statechart/die_at.py` injects it), SIGKILL and Ctrl-C while TLC runs, a janitor that fails to start or dies, and a reader that goes away. Before the fix, the three tests for the paths that broke failed; the two for SIGKILL and Ctrl-C while TLC runs passed already.

## The audited lifecycle model

After adding guard provenance, variable writer lists, refusal probes, and `Assume_*` sensitivity checks (issue #6), `lifecycle/CommandRunAudited.tla` re-audited `statechart.py`, `worker.py`, and `janitor.py` from code rather than trusting `CommandRunFixed.tla` alone:

- **Guard provenance & missing transitions**: adds `MakeFoldersFails` (stage/tmp `mkdir` error), `JanitorDies` (external janitor termination), `CheckKilled` (external signal killing the worker while `SeeCheckEnd` handles `verdict < 0`), `ReadReport` / `ReadReportFails`, and `RenameFails`. Drops `reader` after verifying `_print` catches `OSError` and never alters the exit code.
- **TOCTOU bug fixed in `statechart.py`**: the audit caught that `_run()` previously called `_rename(done, dest)` *before* `open(os.path.join(dest, "report.md"))`, and `_print()` called `os.open`/`os.dup2` unguarded and leaked the `devnull` fd. Any `OSError` there would exit `2` after `dest` was already published, breaking `OutputOnlyOnSuccess`. `_run()` now reads `report.md` from the private `stage/done` directory *before* `_rename()`, and `_print()` closes `devnull` and guards the fallback (`test_report_is_read_before_dest_is_published`).
- **`Assume_*` sensitivity**: `CommandRunAudited.tla` isolates two environmental assumptions — `Assume_NotBothKilled == janitor # "gone"` on `CommandKilled` and `Assume_WorkerPipeOnlyClosesOnCommandDeath == cmd = "killed"` on `WorkerSeesCommandGone`. TLC reaches 199 states and 427 steps (`CommandRunAudited-chart.mmd`, 12 states / 18 arrows; `CommandRunAudited-report.md`): every base rule holds, `FoldersGoAfterCommand` depends on `Assume_NotBothKilled` (while `TLCStopsAfterCommand` and `OutputOnlyOnSuccess` hold even if both are killed), and all holding rules hold even if the worker pipe closes early (`Assume_WorkerPipeOnlyClosesOnCommandDeath`).

## The `Assume_*` check model

`assumptions/AssumeCheck.tla` models `run.py`'s `eliminate()` and `check_assumptions()` loop across two rules (`r1`, `r2`) and two `Assume_*` operators (`a1`, `a2`), including base exit codes `0`/`1`/`2` and `complete`/`cut`/`stop` assumption-run outcomes. TLC reaches 131 states and 404 steps (`assumptions/AssumeCheck-chart.mmd`, 5 states / 6 arrows; `assumptions/AssumeCheck-report.md`), confirming `ExitMatchesBase`, `NoAssumptionsOnBaseError`, `NoAssumptionsWhenNoneHeld`, `NoRedundantCombinedCheck`, `NoDeadlock`, and `AlwaysFinishes`.

To check the models again (with `TLA2TOOLS` or mise for TLC):

- `uv run --no-config --quiet --script plugins/statechart/skills/statechart/scripts/statechart.py notes/statechart/lifecycle/CommandRunFixed.tla --view notes/statechart/lifecycle/view.py --out /tmp/chart-fixed`
- `uv run --no-config --quiet --script plugins/statechart/skills/statechart/scripts/statechart.py notes/statechart/lifecycle/CommandRunAudited.tla --view notes/statechart/lifecycle/view.py --out /tmp/chart-audited`
- `uv run --no-config --quiet --script plugins/statechart/skills/statechart/scripts/statechart.py notes/statechart/assumptions/AssumeCheck.tla --view notes/statechart/assumptions/view.py --out /tmp/chart-assumptions`
