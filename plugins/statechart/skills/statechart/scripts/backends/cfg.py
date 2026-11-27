"""Write the configs and wrapper modules for the TLC runs."""

from __future__ import annotations

from ir import CHART_STATES, RERUN_STATES, ConfigSection, Spec


def config_text(sections: list[ConfigSection], extra: list[str]) -> str:
    lines = [f"{s.key} {' '.join(s.tokens)}" for s in sections]
    lines.extend(extra)
    return "\n".join(lines)


def bound_run(module: str) -> str:
    return "\n".join(
        [
            "---- MODULE ChartBound ----",
            f"EXTENDS {module}",
            "ChartTLC == INSTANCE TLC",
            "ChartNaturals == INSTANCE Naturals",
            f'ChartBound == ChartNaturals!<(ChartTLC!TLCGet("distinct"), {RERUN_STATES})',
            "====",
        ]
    )


def assume_run(module: str, arities: set[int]) -> str:
    lines = [
        "---- MODULE ChartAssume ----",
        f"EXTENDS {module}",
        "ChartTLC == INSTANCE TLC",
        "ChartNaturals == INSTANCE Naturals",
        f'ChartBound == ChartNaturals!<(ChartTLC!TLCGet("distinct"), {RERUN_STATES})',
    ]
    for arity in sorted(arities):
        if arity == 0:
            lines.append("ChartTrue0 == TRUE")
        else:
            params = ", ".join(f"ChartArg{i}" for i in range(1, arity + 1))
            lines.append(f"ChartTrue{arity}({params}) == TRUE")
    lines.append("====")
    return "\n".join(lines)


def chart_run(spec: Spec, tag: str) -> str:
    every = "".join(f'(IF ~{name} THEN {{"{name}"}} ELSE {{}}) \\cup ' for name in spec.invariants)
    return "\n".join(
        [
            "---- MODULE ChartRun ----",
            f"EXTENDS {spec.module}",
            "ChartTLC == INSTANCE TLC",
            "ChartNaturals == INSTANCE Naturals",
            f'ChartBudget == ChartNaturals!<=(ChartTLC!TLCGet("distinct"), {CHART_STATES})',
            f"ChartBroken == {every}{{}}",
            "ChartMark == ChartBroken = {} \\/ "
            f'ChartTLC!PrintT(<<"{tag}", <<{", ".join(spec.variables)}>>, ChartBroken>>)',
            "====",
        ]
    )
