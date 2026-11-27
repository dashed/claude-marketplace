---- MODULE CommandRunAudited ----
\* Audited model of one statechart.py run after applying guard provenance,
\* writer lists, and Assume_* checks to statechart.py, worker.py, and janitor.py.
\*
\* Writer list (every code path that mutates each modeled variable):
\*   cmd     : statechart._run (129-192) sequential phases; OS SIGKILL -> "killed"
\*   check   : statechart._run worker Popen (139), worker.main (59-76),
\*             worker._watch_command (30-42), janitor.main (31-32),
\*             statechart._run kill_group / finally (166, 195), OS kill -> "killed"
\*   janitor : statechart._run janitor Popen (129, 199-200), janitor.main (18-35),
\*             external process death -> "gone"
\*   known   : statechart._run _tell(cleaner, f"pid {check.pid}") (153),
\*             janitor.main line.startswith("pid ") (24-25)
\*   folders : statechart._run os.mkdir(stage) / os.mkdir(tmp) (137-138),
\*             finally rmtree (197-198), janitor.main rmtree (33-34).
\*             Omitted: os.makedirs(dirname(dest), exist_ok=True) (180), empty dir.
\*   out     : statechart._run _rename(done, dest) (182). (stage/draft writes stay
\*             private inside stage until _rename publishes dest.)
\*   stopped : statechart.main on_signal handler for SIGINT/SIGTERM (253-259)
\*   code    : statechart.main / statechart._run return codes (169-192, 267-271)
\*
\* Omitted variable from CommandRunFixed: `reader` (stdout closed by caller).
\* statechart._print (216-225) catches OSError on write/dup2 and never alters
\* exit code or output; verified by test_a_reader_who_stops_reading_does_not_change_the_exit_code.

VARIABLES cmd, check, janitor, known, folders, out, stopped, code
vars == <<cmd, check, janitor, known, folders, out, stopped, code>>

Init ==
    /\ cmd = "start janitor"
    /\ check = "none"
    /\ janitor = "none"
    /\ known = FALSE
    /\ folders = FALSE
    /\ out = "none"
    /\ stopped = FALSE
    /\ code = "none"

Gone == cmd \in {"exited", "killed"}

\* statechart._run (129): subprocess.Popen(janitor.py)
StartJanitor ==
    /\ cmd = "start janitor" \* phase guard: sequential step in _run (129)
    /\ cmd' = "make folders" /\ janitor' = "waiting"
    /\ UNCHANGED <<check, known, folders, out, stopped, code>>

StartJanitorFails ==
    /\ cmd = "start janitor" \* phase guard: Popen raises OSError -> main except (129, 269)
    /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped>>

\* statechart._run (137-138): os.mkdir(stage); os.mkdir(tmp)
MakeFolders ==
    /\ cmd = "make folders" \* phase guard: sequential step after janitor starts (137)
    /\ cmd' = "start check" /\ folders' = TRUE
    /\ UNCHANGED <<check, janitor, known, out, stopped, code>>

MakeFoldersFails ==
    /\ cmd = "make folders" \* phase guard: mkdir raises OSError (137-138) -> finally cleanup (193)
    /\ cmd' = "cleanup" /\ folders' \in {FALSE, TRUE} /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, out, stopped>>

\* statechart._run (139-152): subprocess.Popen(worker.py)
StartCheck ==
    /\ cmd = "start check" \* phase guard: sequential step after folders exist (139)
    /\ cmd' = "tell janitor" /\ check' = "running"
    /\ UNCHANGED <<janitor, known, folders, out, stopped, code>>

StartCheckFails ==
    /\ cmd = "start check" \* phase guard: worker Popen raises OSError (139, 193, 269)
    /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped>>

\* statechart._run (153, 204-213): _tell returns TRUE iff janitor stdin pipe is open
TellJanitor ==
    /\ cmd = "tell janitor"
    /\ janitor = "waiting" \* code check: _tell write/flush succeeds only while janitor lives (209-211)
    /\ cmd' = "wait" /\ known' = TRUE
    /\ UNCHANGED <<check, janitor, folders, out, stopped, code>>

TellJanitorFails ==
    /\ cmd = "tell janitor"
    /\ janitor = "gone" \* code check: _tell catches BrokenPipe/OSError -> raises _CommandError (153-154, 212-213)
    /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped>>

\* worker.main (64, 72-76): check finishes with exit 0/1 ("ok", done exists) or exit 2 ("error", no done)
CheckEnds ==
    /\ check = "running" \* process guard: worker process can finish only while running
    /\ check' \in {"ok", "error"}
    /\ UNCHANGED <<cmd, janitor, known, folders, out, stopped, code>>

\* External signal kills worker process group while running (statechart._run 173-175)
CheckKilled ==
    /\ check = "running" \* process guard: running worker killed externally
    /\ check' = "killed"
    /\ UNCHANGED <<cmd, janitor, known, folders, out, stopped, code>>

\* statechart._run (155-160, 167): wait loop ends when check.wait returns
SeeCheckEnd ==
    /\ cmd = "wait"
    /\ check \in {"ok", "error", "killed"} \* code check: wait loop exits once child returns (157-158)
    /\ cmd' = "decide"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, code>>

\* statechart._run (155, 165-167): stopped set by SIGINT/SIGTERM breaks wait loop and calls kill_group
SeeStop ==
    /\ cmd = "wait"
    /\ stopped \* code check: `while not stopped:` exits when on_signal records signal (155, 253)
    /\ cmd' = "decide"
    /\ check' = IF check = "running" THEN "killed" ELSE check
    /\ UNCHANGED <<janitor, known, folders, out, stopped, code>>

\* statechart._run (169-192): branch on stopped vs verdict
Decide ==
    /\ cmd = "decide"
    /\ \/ stopped /\ cmd' = "cleanup" /\ code' = "130" \* code check: if stopped (169-172)
       \/ ~stopped /\ check = "ok" /\ cmd' = "read report" /\ code' = code \* code check: verdict in (0, 1) and done exists (176)
       \/ ~stopped /\ check # "ok" /\ cmd' = "cleanup" /\ code' = "2" \* code check: verdict < 0 or 2 (173-175, 192)
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped>>

\* statechart._run (177-178): open(done/report.md) BEFORE _rename(done, dest)
ReadReport ==
    /\ cmd = "read report" \* phase guard: read report.md from stage/done before publishing dest
    /\ cmd' = "rename"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, code>>

ReadReportFails ==
    /\ cmd = "read report" \* phase guard: OSError reading done/report.md jumps to finally before _rename
    /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped>>

\* statechart._run (179-189): _rename(done, dest)
Rename ==
    /\ cmd = "rename" \* phase guard: _rename succeeds
    /\ cmd' = "print" /\ out' = "written"
    /\ UNCHANGED <<check, janitor, known, folders, stopped, code>>

RenameFails ==
    /\ cmd = "rename" \* phase guard: _rename raises OSError / _CommandError (181-188) before dest written
    /\ cmd' = "cleanup" /\ code' = "2"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped>>

\* statechart._run (190-191, 216-225): _print catches OSError and never raises
Print ==
    /\ cmd = "print" \* phase guard: _print finishes and returns verdict
    /\ cmd' = "cleanup" /\ code' = "verdict"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped>>

\* statechart._run (193-201): finally block kills worker, removes stage/tmp, kills janitor
Cleanup ==
    /\ cmd = "cleanup"
    /\ cmd' = "exited" /\ folders' = FALSE
    /\ check' = IF check = "running" THEN "killed" ELSE check
    /\ janitor' = IF janitor = "waiting" THEN "gone" ELSE janitor
    /\ UNCHANGED <<known, out, stopped, code>>

\* statechart.main (253-259): user sends SIGINT/SIGTERM while command process exists
PressCtrlC ==
    /\ ~stopped /\ ~Gone \* process guard: live command catches signal once
    /\ stopped' = TRUE
    /\ UNCHANGED <<cmd, check, janitor, known, folders, out, code>>

\* External termination of janitor process before cleanup
JanitorDies ==
    /\ janitor = "waiting" /\ ~Gone \* process guard: running janitor process can die externally
    /\ janitor' = "gone"
    /\ UNCHANGED <<cmd, check, known, folders, out, stopped, code>>

\* Environmental assumption: operator/OS does not kill both janitor and command externally
Assume_NotBothKilled == janitor # "gone"

CommandKilled ==
    /\ ~Gone
    /\ Assume_NotBothKilled
    /\ cmd' = "killed"
    /\ UNCHANGED <<check, janitor, known, folders, out, stopped, code>>

\* Environmental assumption: worker stdin pipe only closes when command dies
Assume_WorkerPipeOnlyClosesOnCommandDeath == cmd = "killed"

\* worker._watch_command (30-42): pipe EOF kills worker process group
WorkerSeesCommandGone ==
    /\ check = "running"
    /\ Assume_WorkerPipeOnlyClosesOnCommandDeath
    /\ check' = "killed"
    /\ UNCHANGED <<cmd, janitor, known, folders, out, stopped, code>>

\* janitor.main (22-35): stdin EOF triggers kill_group(pid) (if known) and rmtree(stage, tmp)
JanitorCleansUp ==
    /\ janitor = "waiting" /\ cmd = "killed" \* code check: janitor stdin closes only when parent exits/dies (22)
    /\ janitor' = "gone" /\ folders' = FALSE
    /\ check' = IF known /\ check = "running" THEN "killed" ELSE check
    /\ UNCHANGED <<cmd, known, out, stopped, code>>

Settled == Gone /\ janitor # "waiting" /\ (cmd = "exited" => check # "running")
Done == Settled /\ UNCHANGED vars

Next ==
    \/ StartJanitor \/ StartJanitorFails \/ MakeFolders \/ MakeFoldersFails
    \/ StartCheck \/ StartCheckFails \/ TellJanitor \/ TellJanitorFails
    \/ CheckEnds \/ CheckKilled \/ SeeCheckEnd \/ SeeStop \/ Decide
    \/ ReadReport \/ ReadReportFails \/ Rename \/ RenameFails \/ Print \/ Cleanup
    \/ PressCtrlC \/ JanitorDies \/ CommandKilled \/ WorkerSeesCommandGone
    \/ JanitorCleansUp \/ Done

Spec ==
    /\ Init /\ [][Next]_vars
    /\ WF_vars(JanitorCleansUp) /\ WF_vars(Cleanup) /\ WF_vars(WorkerSeesCommandGone)

OutputOnlyOnSuccess == (cmd = "exited" /\ code \in {"2", "130"}) => out = "none"
TLCStopsAfterCommand == Gone ~> check # "running"
FoldersGoAfterCommand == Gone ~> ~folders
====
