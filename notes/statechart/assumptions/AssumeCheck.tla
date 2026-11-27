---- MODULE AssumeCheck ----
\* Dogfood model of run.py's base check + check_assumptions() + report.py contract
\* for two rules (r1, r2) and two first-order Assume_* operators (a1, a2).
\*
\* Writer list (every code path in run.py / report.py that writes each variable):
\*   phase           : run.check -> eliminate (519), exit check (537), check_assumptions (540-577)
\*   baseExit        : run.check exit_ = _exit_class(judged.first.status) (521)
\*   r1, r2          : run.check eliminate() base verdict loop (436-508)
\*   s1Broke         : run.check check_assumptions -> check_relaxed([a1], ...) (557-572)
\*   s2Broke         : run.check check_assumptions -> check_relaxed([a2], ...) (557-572)
\*   combChecked     : run.check check_assumptions -> remaining = [r for r in held_rules if r not in broken_single] (575-579)
\*   lastOutcome     : run.check eliminate() status ("complete", "cut", "stop") for assumption runs
\*   ranAssumptions  : run.check check_assumptions (540-581), TRUE iff check_relaxed ran at least once
\*   exitCode        : run.check result() -> CheckResult.exit = exit_ (521, 591), pipeline.py -> worker.py
\*
\* Omitted details: exact rule/operator string names, SANY XML discovery (spec.py),
\* bounded rule-elimination sub-iterations inside check_relaxed (modeled as one step
\* returning final broken subset + cut/stop outcome).

VARIABLES phase, baseExit, r1, r2, s1Broke, s2Broke, combChecked, lastOutcome, ranAssumptions, exitCode
vars == <<phase, baseExit, r1, r2, s1Broke, s2Broke, combChecked, lastOutcome, ranAssumptions, exitCode>>

Rules == {"r1", "r2"}
Held == (IF r1 = "holds" THEN {"r1"} ELSE {}) \cup (IF r2 = "holds" THEN {"r2"} ELSE {})

Init ==
    /\ phase = "base"
    /\ baseExit = "none"
    /\ r1 = "none"
    /\ r2 = "none"
    /\ s1Broke = {}
    /\ s2Broke = {}
    /\ combChecked = {}
    /\ lastOutcome = "none"
    /\ ranAssumptions = FALSE
    /\ exitCode = "none"

\* run.check (519-538): base eliminate() + if exit_ == 2: raise failed(judged.first)
BaseCheck ==
    /\ phase = "base" \* phase guard: sequential start of run.check
    /\ \/ /\ baseExit' = "2" \* code path: _exit_class(judged.first.status) == 2 raises StatechartError
          /\ r1' = "not checked" /\ r2' = "not checked"
          /\ exitCode' = "2" /\ phase' = "done"
       \/ /\ baseExit' = "0" \* code path: exit_ == 0 -> all rules held
          /\ r1' = "holds" /\ r2' = "holds"
          /\ exitCode' = "0" /\ phase' = "assume1"
       \/ /\ baseExit' = "1" \* code path: exit_ == 1 -> at least one rule broke; others hold or not checked
          /\ r1' \in {"holds", "broken", "not checked"}
          /\ r2' \in {"holds", "broken", "not checked"}
          /\ (r1' = "broken" \/ r2' = "broken")
          /\ exitCode' = "1"
          /\ phase' = IF (r1' = "holds" \/ r2' = "holds") THEN "assume1" ELSE "done"
    /\ UNCHANGED <<s1Broke, s2Broke, combChecked, lastOutcome, ranAssumptions>>

\* run.check check_assumptions (572): first single Assume_* relaxation on Held
RunAssume1 ==
    /\ phase = "assume1"
    /\ Held # {} \* code guard: check_assumptions returns [] if not held_rules (542)
    /\ s1Broke' \in SUBSET Held
    /\ lastOutcome' \in {"complete", "cut", "stop"}
    /\ ranAssumptions' = TRUE
    /\ phase' = "assume2"
    /\ UNCHANGED <<baseExit, r1, r2, s2Broke, combChecked, exitCode>>

\* run.check check_assumptions (572-579): second single Assume_* relaxation + skip check for combined
RunAssume2 ==
    /\ phase = "assume2" \* phase guard: sequential loop over spec.assumptions
    /\ s2Broke' \in SUBSET Held
    /\ lastOutcome' \in {"complete", "cut", "stop"}
    /\ ranAssumptions' = TRUE
    /\ LET rem == Held \ (s1Broke \cup s2Broke') IN
       phase' = IF rem # {} THEN "combined" ELSE "done"
    /\ UNCHANGED <<baseExit, r1, r2, s1Broke, combChecked, exitCode>>

\* run.check check_assumptions (576-579): combined relaxation only on rules surviving every single run
RunCombined ==
    /\ phase = "combined"
    /\ LET rem == Held \ (s1Broke \cup s2Broke) IN
       /\ rem # {} \* code guard: `if remaining:` (576)
       /\ combChecked' = rem
       /\ lastOutcome' \in {"complete", "cut", "stop"}
       /\ ranAssumptions' = TRUE
       /\ phase' = "done"
    /\ UNCHANGED <<baseExit, r1, r2, s1Broke, s2Broke, exitCode>>

Done == phase = "done" /\ UNCHANGED vars

Next == BaseCheck \/ RunAssume1 \/ RunAssume2 \/ RunCombined \/ Done

Spec ==
    /\ Init /\ [][Next]_vars
    /\ WF_vars(BaseCheck) /\ WF_vars(RunAssume1) /\ WF_vars(RunAssume2) /\ WF_vars(RunCombined)

\* Rules:
\* 1. Assumption reruns never change the command's exit code.
ExitMatchesBase == (phase = "done") => (exitCode = baseExit)

\* 2. Base TLC errors never run assumption checks.
NoAssumptionsOnBaseError == (baseExit = "2") => ~ranAssumptions

\* 3. When no rules held in base, no assumption checks run.
NoAssumptionsWhenNoneHeld == (phase = "done" /\ Held = {}) => ~ranAssumptions

\* 4. Combined check never re-tests a rule already broken by a single assumption.
NoRedundantCombinedCheck == (combChecked \cap (s1Broke \cup s2Broke)) = {}

\* 5. Every run eventually finishes.
AlwaysFinishes == (phase = "base") ~> (phase = "done")
====
