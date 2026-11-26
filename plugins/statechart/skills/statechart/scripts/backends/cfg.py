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
