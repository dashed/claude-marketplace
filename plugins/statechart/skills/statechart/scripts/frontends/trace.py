"""Read a counterexample that may loop."""

from __future__ import annotations

import re
from collections.abc import Iterable

from frontends.messages import action_of, message_state, text_of
from ir import EC, Part, Trace, TraceSeqState

_BACK = re.compile(r"([0-9]+): Back to state: ")


def read_trace(messages: Iterable[Part]) -> Trace:
    seq: list[TraceSeqState] = []
    for m in messages:
        if isinstance(m, str):
            continue
        if m.code == EC.TLC_STATE_PRINT3:
            return Trace(seq, len(seq) - 1)
        back = _BACK.match(text_of(m)) if m.code == EC.TLC_BACK_TO_STATE else None
        if back:
            loop = int(back.group(1)) - 1
            vars = seq[loop].vars if 0 <= loop < len(seq) else None
            seq.append(TraceSeqState(action_of(m) or "", vars))
            return Trace(seq, loop)
        action = action_of(m) if m.code == EC.TLC_STATE_PRINT2 else None
        if action is not None:
            seq.append(TraceSeqState(action, message_state(m)))
        elif m.code in (EC.TLC_INVARIANT_VIOLATED_INITIAL, EC.TLC_PROPERTY_VIOLATED_INITIAL):
            seq.append(TraceSeqState("", message_state(m)))
    return Trace(seq, None)
