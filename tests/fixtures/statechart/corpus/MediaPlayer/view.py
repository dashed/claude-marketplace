import re

_WORDS = re.compile(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[A-Z])(?=[A-Z][a-z])")


def state(v):
    return {"Playback": v["playback"], "Volume": v["volume"]}


def step(action, from_, to):
    return _WORDS.sub(" ", action).lower()
