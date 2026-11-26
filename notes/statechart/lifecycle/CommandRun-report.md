# CommandRun

TLC reached 208 states and 433 steps. The chart draws 9 states and 20 arrows.
The chart does not draw 255 steps that stay in one chart state.

## OutputOnlyOnSuccess breaks
The shortest path has 9 steps:
0. Starting TLC
1. the reader of stdout goes away: Starting TLC
2. the command starts TLC: Starting the janitor
3. TLC finishes: Starting the janitor
4. the command starts the janitor: Waiting for TLC
5. TLC ends: Reading the result
6. TLC passed or found a bug: Writing the output
7. the check passed or found a bug: Printing the report
8. nobody reads stdout any more: Cleaning up
9. the command removes its folders: Ended

## TLCStopsAfterCommand breaks
TLC's counterexample is in tlc-TLCStopsAfterCommand.out. It has 4 steps:
0. Starting TLC
1. the reader of stdout goes away: Starting TLC
2. you press Ctrl-C: Starting TLC
3. the command starts TLC: Starting the janitor
4. something kills the command: Killed
The run stops in "Killed" forever.

## FoldersGoAfterCommand breaks
TLC's counterexample is in tlc-FoldersGoAfterCommand.out. It has 6 steps:
0. Starting TLC
1. the reader of stdout goes away: Starting TLC
2. you press Ctrl-C: Starting TLC
3. the command starts TLC: Starting the janitor
4. starting the janitor fails: Cleaning up
5. something kills the command: Killed
6. TLC finishes: Killed
The run stops in "Killed" forever.

## Rules that hold
NoDeadlock
