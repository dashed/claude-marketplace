---- MODULE CommandRun ----
\* statechart.py as first ported to Python: the command, the worker that runs TLC (its process group),
\* the janitor, and what can happen to them from outside.
VARIABLES cmd, check, janitor, folders, out, stopped, reader, code
vars == <<cmd, check, janitor, folders, out, stopped, reader, code>>

Init ==
    /\ cmd = "start check"
    /\ check = "none"
    /\ janitor = "none"
    /\ folders = TRUE          \* the stage folder beside --out and the temp folder
    /\ out = "none"
    /\ stopped = FALSE
    /\ reader = TRUE           \* someone still reads stdout
    /\ code = "none"

Gone == cmd \in {"exited", "killed"}

StartCheck ==
    /\ cmd = "start check" /\ cmd' = "start janitor" /\ check' = "running"
    /\ UNCHANGED <<janitor, folders, out, stopped, reader, code>>
StartCheckFails ==
    /\ cmd = "start check" /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, folders, out, stopped, reader>>
StartJanitor ==
    /\ cmd = "start janitor" /\ cmd' = "wait" /\ janitor' = "waiting"
    /\ UNCHANGED <<check, folders, out, stopped, reader, code>>
StartJanitorFails ==
    /\ cmd = "start janitor" /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, folders, out, stopped, reader>>
CheckEnds ==
    /\ check = "running" /\ check' \in {"ok", "error"}
    /\ UNCHANGED <<cmd, janitor, folders, out, stopped, reader, code>>
SeeCheckEnd ==
    /\ cmd = "wait" /\ check \in {"ok", "error"} /\ cmd' = "decide"
    /\ UNCHANGED <<check, janitor, folders, out, stopped, reader, code>>
SeeStop ==
    /\ cmd = "wait" /\ stopped /\ cmd' = "decide"
    /\ check' = IF check = "running" THEN "killed" ELSE check
    /\ UNCHANGED <<janitor, folders, out, stopped, reader, code>>
Decide ==
    /\ cmd = "decide"
    /\ \/ stopped /\ cmd' = "cleanup" /\ code' = "130"
       \/ ~stopped /\ check = "ok" /\ cmd' = "rename" /\ code' = code
       \/ ~stopped /\ check # "ok" /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, folders, out, stopped, reader>>
Rename ==
    /\ cmd = "rename" /\ cmd' = "print" /\ out' = "written"
    /\ UNCHANGED <<check, janitor, folders, stopped, reader, code>>
Print ==
    /\ cmd = "print" /\ cmd' = "cleanup"
    /\ code' = IF reader THEN "verdict" ELSE "2"
    /\ UNCHANGED <<check, janitor, folders, out, stopped, reader>>
Cleanup ==
    /\ cmd = "cleanup" /\ cmd' = "exited" /\ folders' = FALSE
    /\ janitor' = IF janitor = "waiting" THEN "gone" ELSE janitor
    /\ UNCHANGED <<check, out, stopped, reader, code>>
PressCtrlC ==
    /\ ~stopped /\ ~Gone /\ stopped' = TRUE
    /\ UNCHANGED <<cmd, check, janitor, folders, out, reader, code>>
CommandKilled ==
    /\ ~Gone /\ cmd' = "killed"
    /\ UNCHANGED <<check, janitor, folders, out, stopped, reader, code>>
ReaderLeaves ==
    /\ reader /\ ~Gone /\ reader' = FALSE
    /\ UNCHANGED <<cmd, check, janitor, folders, out, stopped, code>>
JanitorCleansUp ==
    /\ janitor = "waiting" /\ cmd = "killed" /\ janitor' = "gone" /\ folders' = FALSE
    /\ check' = IF check = "running" THEN "killed" ELSE check
    /\ UNCHANGED <<cmd, out, stopped, reader, code>>

Settled == Gone /\ janitor # "waiting"
Done == Settled /\ UNCHANGED vars

Next ==
    \/ StartCheck \/ StartCheckFails \/ StartJanitor \/ StartJanitorFails
    \/ CheckEnds \/ SeeCheckEnd \/ SeeStop \/ Decide \/ Rename \/ Print \/ Cleanup
    \/ PressCtrlC \/ CommandKilled \/ ReaderLeaves \/ JanitorCleansUp \/ Done

OutputOnlyOnSuccess == (cmd = "exited" /\ code \in {"2", "130"}) => out = "none"
Spec == Init /\ [][Next]_vars /\ WF_vars(JanitorCleansUp) /\ WF_vars(Cleanup)

TLCStopsAfterCommand == Gone ~> check # "running"
FoldersGoAfterCommand == Gone ~> ~folders
====
