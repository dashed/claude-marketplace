_COMMAND = {
    "start check": "Starting TLC",
    "start janitor": "Starting the janitor",
    "make folders": "Making its folders",
    "tell janitor": "Telling the janitor about TLC",
    "wait": "Waiting for TLC",
    "decide": "Reading the result",
    "rename": "Writing the output",
    "print": "Printing the report",
    "cleanup": "Cleaning up",
    "exited": "Ended",
    "killed": "Killed",
}
_STEPS = {
    "StartCheck": "the command starts TLC",
    "StartCheckFails": "starting TLC fails",
    "StartJanitor": "the command starts the janitor",
    "StartJanitorFails": "starting the janitor fails",
    "MakeFolders": "the command makes its folders",
    "TellJanitor": "the command tells the janitor",
    "TellJanitorFails": "the janitor is gone",
    "CheckEnds": "TLC finishes",
    "ReaderLeaves": "the reader of stdout goes away",
    "PressCtrlC": "you press Ctrl-C",
    "WorkerSeesCommandGone": "TLC stops itself",
    "SeeCheckEnd": "TLC ends",
    "SeeStop": "the command stops TLC",
    "Rename": "the check passed or found a bug",
    "Print": "the report prints",
    "Cleanup": "the command removes its folders",
    "CommandKilled": "something kills the command",
    "JanitorCleansUp": "the janitor kills TLC and removes the folders",
}


def state(v):
    return _COMMAND[v["cmd"]]


def step(action, from_, to):
    if action == "Decide":
        if to["cmd"] == "rename":
            return "TLC passed or found a bug"
        return "you pressed Ctrl-C" if to["code"] == "130" else "TLC failed"
    if action == "Print" and to["code"] == "2":
        return "nobody reads stdout any more"
    return _STEPS.get(action, action)


title = "statechart.py: one run of the command"
