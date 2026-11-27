_COMMAND = {
    "start janitor": "The command starts the janitor process",
    "make folders": "The command makes the stage and temp folders",
    "start check": "The command starts the worker, which runs TLC",
    "tell janitor": "The command sends the worker's pid to the janitor",
    "wait": "The command waits for TLC to finish",
    "decide": "The command reads TLC's exit code",
    "read report": "The command reads the report before publishing --out",
    "rename": "The command moves the chart and report into --out",
    "print": "The command prints the report to stdout",
    "cleanup": "The command removes its folders",
    "exited": "The command has removed its folders and exited",
    "killed": "The command is dead, and the janitor and TLC may still run",
}
_STEPS = {
    "StartJanitor": "the janitor process starts",
    "StartJanitorFails": "the janitor process fails to start",
    "MakeFolders": "both folders exist",
    "MakeFoldersFails": "creating the stage or temp folder fails",
    "StartCheck": "the worker starts and runs TLC",
    "StartCheckFails": "the worker fails to start",
    "TellJanitor": "the janitor gets the worker's pid",
    "TellJanitorFails": "the janitor is gone and cannot get the pid",
    "CheckEnds": "TLC finishes its check",
    "CheckKilled": "an external signal kills the worker",
    "JanitorDies": "the janitor dies before the command ends",
    "ReaderLeaves": "the program that reads stdout exits (as with | head)",
    "PressCtrlC": "you press Ctrl-C",
    "WorkerSeesCommandGone": "the worker sees the command's pipe close and kills TLC",
    "SeeCheckEnd": "TLC exits",
    "SeeStop": "the command kills TLC after Ctrl-C",
    "ReadReport": "the command finishes reading the report",
    "ReadReportFails": "reading the report fails",
    "Rename": "the files are in --out",
    "RenameFails": "moving the files into --out fails",
    "Print": "the report is on stdout",
    "Cleanup": "the folders are gone and the command exits",
    "CommandKilled": "SIGKILL or a crash ends the command",
    "JanitorCleansUp": "the janitor kills TLC and removes the folders",
}


def state(v):
    label = _COMMAND[v["cmd"]]
    return label if v["cmd"] in ("exited", "killed") else ["The command is alive", label]


def step(action, from_, to):
    if action == "Decide":
        if to["cmd"] in ("rename", "read report"):
            return "TLC passed or found a bug (exit 0 or 1)"
        if to["code"] == "130":
            return "you pressed Ctrl-C (exit 130)"
        return "TLC failed (exit 2)"
    if action == "Print" and to["code"] == "2":
        return "printing fails because nobody reads stdout (exit 2)"
    return _STEPS.get(action, action)


title = "statechart.py: one run of the command"
