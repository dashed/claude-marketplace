# CommandRun

TLC reached 208 states and 433 steps. The chart draws 9 states and 14 arrows.
The chart does not draw 255 steps that stay in one chart state.

## OutputOnlyOnSuccess breaks
The shortest path has 9 steps:
0. The command is alive / The command starts the worker, which runs TLC
1. the program that reads stdout exits (as with | head): The command is alive / The command starts the worker, which runs TLC
2. the worker starts and runs TLC: The command is alive / The command starts the janitor process
3. TLC finishes its check: The command is alive / The command starts the janitor process
4. the janitor process starts: The command is alive / The command waits for TLC to finish
5. TLC exits: The command is alive / The command reads TLC's exit code
6. TLC passed or found a bug (exit 0 or 1): The command is alive / The command moves the chart and report into --out
7. the files are in --out: The command is alive / The command prints the report to stdout
8. printing fails because nobody reads stdout (exit 2): The command is alive / The command removes its folders
9. the folders are gone and the command exits: The command has removed its folders and exited

## TLCStopsAfterCommand breaks
TLC's counterexample is in tlc-TLCStopsAfterCommand.out. It has 4 steps:
0. The command is alive / The command starts the worker, which runs TLC
1. the program that reads stdout exits (as with | head): The command is alive / The command starts the worker, which runs TLC
2. you press Ctrl-C: The command is alive / The command starts the worker, which runs TLC
3. the worker starts and runs TLC: The command is alive / The command starts the janitor process
4. SIGKILL or a crash ends the command: The command is dead, and the janitor and TLC may still run
The run stops in "The command is dead, and the janitor and TLC may still run" forever.

## FoldersGoAfterCommand breaks
TLC's counterexample is in tlc-FoldersGoAfterCommand.out. It has 6 steps:
0. The command is alive / The command starts the worker, which runs TLC
1. the program that reads stdout exits (as with | head): The command is alive / The command starts the worker, which runs TLC
2. you press Ctrl-C: The command is alive / The command starts the worker, which runs TLC
3. the worker starts and runs TLC: The command is alive / The command starts the janitor process
4. the janitor process fails to start: The command is alive / The command removes its folders
5. SIGKILL or a crash ends the command: The command is dead, and the janitor and TLC may still run
6. TLC finishes its check: The command is dead, and the janitor and TLC may still run
The run stops in "The command is dead, and the janitor and TLC may still run" forever.

## Rules that hold
NoDeadlock
