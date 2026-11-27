# CommandRunAudited

TLC reached 199 states and 427 steps. The chart draws 12 states and 18 arrows.
The chart does not draw 244 steps that stay in one chart state.

## Rules that hold
OutputOnlyOnSuccess, NoDeadlock, TLCStopsAfterCommand, FoldersGoAfterCommand

## Assumptions
- FoldersGoAfterCommand holds only under Assume_NotBothKilled.
- Every holding rule still holds without Assume_WorkerPipeOnlyClosesOnCommandDeath.
