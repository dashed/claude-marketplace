---- MODULE CommandRunFixed ----
\* The fix: the janitor starts before any folder exists and learns the worker's pid
\* afterwards; the worker kills its own process group when the command's pipe closes;
\* cleanup kills a check that is still running; a report that cannot print does not
\* change the exit code.
VARIABLES cmd, check, janitor, known, folders, out, stopped, reader, code
vars == <<cmd, check, janitor, known, folders, out, stopped, reader, code>>

Init ==
    /\ cmd = "start janitor"
    /\ check = "none"
    /\ janitor = "none"
    /\ known = FALSE          \* the janitor knows the worker's pid
    /\ folders = FALSE
    /\ out = "none"
    /\ stopped = FALSE
    /\ reader = TRUE
    /\ code = "none"

Gone == cmd \in {"exited", "killed"}

StartJanitor ==
    /\ cmd = "start janitor" /\ cmd' = "make folders" /\ janitor' = "waiting"
    /\ UNCHANGED <<check, known, folders, out, stopped, reader, code>>
StartJanitorFails ==
    /\ cmd = "start janitor" /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, reader>>
MakeFolders ==
    /\ cmd = "make folders" /\ cmd' = "start check" /\ folders' = TRUE
    /\ UNCHANGED <<check, janitor, known, out, stopped, reader, code>>
StartCheck ==
    /\ cmd = "start check" /\ cmd' = "tell janitor" /\ check' = "running"
    /\ UNCHANGED <<janitor, known, folders, out, stopped, reader, code>>
StartCheckFails ==
    /\ cmd = "start check" /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, reader>>
TellJanitor ==
    /\ cmd = "tell janitor" /\ cmd' = "wait" /\ known' = TRUE
    /\ UNCHANGED <<check, janitor, folders, out, stopped, reader, code>>
TellJanitorFails ==
    /\ cmd = "tell janitor" /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, reader>>
CheckEnds ==
    /\ check = "running" /\ check' \in {"ok", "error"}
    /\ UNCHANGED <<cmd, janitor, known, folders, out, stopped, reader, code>>
SeeCheckEnd ==
    /\ cmd = "wait" /\ check \in {"ok", "error"} /\ cmd' = "decide"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, reader, code>>
SeeStop ==
    /\ cmd = "wait" /\ stopped /\ cmd' = "decide"
    /\ check' = IF check = "running" THEN "killed" ELSE check
    /\ UNCHANGED <<janitor, known, folders, out, stopped, reader, code>>
Decide ==
    /\ cmd = "decide"
    /\ \/ stopped /\ cmd' = "cleanup" /\ code' = "130"
       \/ ~stopped /\ check = "ok" /\ cmd' = "rename" /\ code' = code
       \/ ~stopped /\ check # "ok" /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, reader>>
Rename ==
    /\ cmd = "rename" /\ cmd' = "print" /\ out' = "written"
    /\ UNCHANGED <<check, janitor, known, folders, stopped, reader, code>>
Print ==
    /\ cmd = "print" /\ cmd' = "cleanup" /\ code' = "verdict"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, reader>>
Cleanup ==
    /\ cmd = "cleanup" /\ cmd' = "exited" /\ folders' = FALSE
    /\ check' = IF check = "running" THEN "killed" ELSE check
    /\ janitor' = IF janitor = "waiting" THEN "gone" ELSE janitor
    /\ UNCHANGED <<known, out, stopped, reader, code>>
PressCtrlC ==
    /\ ~stopped /\ ~Gone /\ stopped' = TRUE
    /\ UNCHANGED <<cmd, check, janitor, known, folders, out, reader, code>>
CommandKilled ==
    /\ ~Gone /\ cmd' = "killed"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, reader, code>>
ReaderLeaves ==
    /\ reader /\ ~Gone /\ reader' = FALSE
    /\ UNCHANGED <<cmd, check, janitor, known, folders, out, stopped, code>>
JanitorCleansUp ==
    /\ janitor = "waiting" /\ cmd = "killed" /\ janitor' = "gone" /\ folders' = FALSE
    /\ check' = IF known /\ check = "running" THEN "killed" ELSE check
    /\ UNCHANGED <<cmd, known, out, stopped, reader, code>>
WorkerSeesCommandGone ==
    /\ cmd = "killed" /\ check = "running" /\ check' = "killed"
    /\ UNCHANGED <<cmd, janitor, known, folders, out, stopped, reader, code>>

Settled == Gone /\ janitor # "waiting"
Done == Settled /\ UNCHANGED vars

Next ==
    \/ StartJanitor \/ StartJanitorFails \/ MakeFolders \/ StartCheck \/ StartCheckFails
    \/ TellJanitor \/ TellJanitorFails \/ CheckEnds \/ SeeCheckEnd \/ SeeStop \/ Decide
    \/ Rename \/ Print \/ Cleanup \/ PressCtrlC \/ CommandKilled \/ ReaderLeaves
    \/ JanitorCleansUp \/ WorkerSeesCommandGone \/ Done

Spec ==
    /\ Init /\ [][Next]_vars
    /\ WF_vars(JanitorCleansUp) /\ WF_vars(Cleanup) /\ WF_vars(WorkerSeesCommandGone)

OutputOnlyOnSuccess == (cmd = "exited" /\ code \in {"2", "130"}) => out = "none"
TLCStopsAfterCommand == Gone ~> check # "running"
FoldersGoAfterCommand == Gone ~> ~folders
====
