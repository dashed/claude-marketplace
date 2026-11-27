_PHASES = {
    "base": "The command runs the base TLC check",
    "assume1": "The command rechecks holding rules without the first assumption",
    "assume2": "The command rechecks holding rules without the second assumption",
    "combined": "The command rechecks surviving rules without either assumption",
    "done": "The command writes the report and exits",
}


def state(v):
    return _PHASES[v["phase"]]


def step(action, from_, to):
    if action == "BaseCheck":
        if to["baseExit"] == "2":
            return "the base check fails (exit 2)"
        if to["phase"] == "done":
            return "every rule breaks in the base check (exit 1)"
        return (
            "every rule holds in the base check (exit 0)"
            if to["baseExit"] == "0"
            else "some rules hold and others break (exit 1)"
        )
    if action == "RunAssume1":
        return "the first assumption check finishes"
    if action == "RunAssume2":
        return (
            "every base-holding rule already broke under one relaxation"
            if to["phase"] == "done"
            else "some base-holding rules survived both single checks"
        )
    if action == "RunCombined":
        return "the combined assumption check finishes"
    return action


title = "run.py: base check and assumption sensitivity pass"
