"""Run SANY and TLC, and read what they print."""

from __future__ import annotations

import errno
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import BinaryIO

import js
from backends.cfg import assume_run, bound_run, chart_run, config_text
from backends.plain_text import plain_text
from frontends.config import read_config
from frontends.dot import parse_dot
from frontends.marks import read_counterexample, read_marks
from frontends.messages import read_messages
from frontends.spec import initial_only_properties, read_checks, read_sany, read_spec
from frontends.trace import read_trace
from frontends.verdict import Break, read_verdict
from ir import (
    CHART_STATES,
    LEVEL,
    PART,
    RERUN_STATES,
    Assumption,
    AssumptionCheck,
    Bug,
    CheckResult,
    ConfigSection,
    Drawing,
    Graph,
    Lasso,
    Mark,
    Part,
    Property,
    Rule,
    StatechartError,
    States,
    Stop,
    Trace,
    TraceSeqState,
    Verdict,
    has_section,
    must,
    rule_key,
    state_rules,
)
from passes.annotate import add_past, dead_ends, finder, lasso, mark
from passes.paths import path_graph


def _decode(data: bytes) -> str:
    text = data.decode("utf-8", "replace")
    return text[:-1] if text.endswith("\r") else text


def _lines(chunks: Iterable[bytes]) -> Iterator[str]:
    """The lines of a byte stream, split as `split_lines` in frontends/dot.py splits them."""
    rest = b""
    for chunk in chunks:
        buf = rest + chunk if rest else chunk
        cut = buf.rfind(b"\n")
        if cut == -1:
            rest = buf
            continue
        for line in buf[:cut].split(b"\n"):
            yield _decode(line)
        rest = buf[cut + 1 :]
    yield _decode(rest)


def _chunks(file: BinaryIO, size: int) -> Iterator[bytes]:
    pos = 0
    while pos < size:
        file.seek(pos)
        data = file.read(min(PART, size - pos))
        if not data:
            break
        pos += len(data)
        yield data


def file_lines(file: str) -> Iterator[str]:
    with open(file, "rb") as f:
        yield from _lines(_chunks(f, os.fstat(f.fileno()).st_size))


TLC_TOOL = (
    "http:tla2tools[url=https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar,"
    "checksum=sha256:936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88]@1.7.4"
)
JAVA_TOOL = "java@temurin-25"
PINNED_FLAGS = ["-workers", "1", "-fp", "0", "-lncheck", "final"]
_SANY_ERRORS = re.compile(js.BOL + r"\*\*\* ?(?:Errors|Abort messages|Parse Error)")
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _spawn_error(file: str, error: OSError) -> str:
    """The message that Node gives when it cannot start `file`."""
    code = errno.errorcode.get(error.errno or 0)
    return f"spawn {file} {code}" if code else f"spawn {file}: {error}"


@dataclass(eq=False)
class _ChildResult:
    status: int | None
    stdout: str
    stderr: str
    error: str | None


def _run_child(file: str, args: list[str], cwd: str, env: Mapping[str, str]) -> _ChildResult:
    try:
        r = subprocess.run(
            [file, *args],
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            creationflags=_NO_WINDOW,
            check=False,
        )
    except OSError as error:
        return _ChildResult(None, "", "", _spawn_error(file, error))
    status = r.returncode if r.returncode >= 0 else None
    stdout = r.stdout.decode("utf-8", "replace")
    stderr = r.stderr.decode("utf-8", "replace")
    return _ChildResult(status, stdout, stderr, None)


def message_of(error: BaseException) -> str:
    if isinstance(error, (StatechartError, OSError)):
        return str(error)
    return f"{type(error).__name__}: {error}"


class Output:
    """The bytes that a TLC run printed, read again each time it is iterated."""

    def __init__(self, files: list[str]) -> None:
        self._files: list[tuple[BinaryIO, int]] = []
        for f in files:
            handle = open(f, "rb")
            self._files.append((handle, os.fstat(handle.fileno()).st_size))

    def __iter__(self) -> Iterator[bytes]:
        for handle, size in self._files:
            yield from _chunks(handle, size)


class Messages:
    """TLC's messages from a run's output, read again each time."""

    def __init__(self, output: Output) -> None:
        self._output = output

    def __iter__(self) -> Iterator[Part]:
        return read_messages(_lines(self._output))


@dataclass(eq=False)
class FileResult:
    status: int | None
    stdout: str
    output: Output
    error: str | None


def _run_to_files(
    file: str, args: list[str], out: str, cwd: str, env: Mapping[str, str]
) -> FileResult:
    files = [f"{out}.stdout", f"{out}.stderr"]
    error: str | None = None
    status: int | None = None
    with open(files[0], "wb") as stdout, open(files[1], "wb") as stderr:
        try:
            child = subprocess.Popen(
                [file, *args],
                cwd=cwd,
                env=dict(env),
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=_NO_WINDOW,
            )
        except OSError as e:
            error = _spawn_error(file, e)
        else:
            code = child.wait()
            status = code if code >= 0 else None
    return FileResult(status, files[0], Output(files), error)


@dataclass(eq=False)
class _Tlc:
    jar: str
    java: str


def _find_tlc(cwd: str) -> _Tlc:
    jar = os.environ.get("TLA2TOOLS")
    java = os.environ.get("JAVA")
    if jar:
        return _Tlc(jar, java or "java")
    env = {**os.environ, "MISE_CEILING_PATHS": cwd}

    def mise(*args: str) -> _ChildResult:
        return _run_child("mise", list(args), cwd, env)

    def where() -> list[_ChildResult]:
        return [mise("where", TLC_TOOL), mise("which", "java", "--tool", JAVA_TOOL)]

    found = where()
    if any(r.status != 0 for r in found):
        r = mise("install", JAVA_TOOL, TLC_TOOL)
        if r.status != 0:
            raise StatechartError(
                f"Cannot find TLC: mise install failed: {r.error or js.trim(r.stderr)}\n"
                "Or set TLA2TOOLS to the path of tla2tools.jar, and JAVA to a java binary "
                "(Java 11 or later)."
            )
        found = where()
    return _Tlc(
        os.path.join(js.trim(found[0].stdout), "tla2tools.jar"),
        java or js.trim(found[1].stdout),
    )


def _exit_class(status: int | None) -> int:
    return 0 if status == 0 else 1 if status in (11, 12, 13) else 2


def _tail(r: FileResult) -> str:
    if r.error:
        return r.error
    kept: list[str] = []
    size = 0
    for chunk in plain_text(Messages(r.output)):
        kept.append(chunk)
        size += len(chunk)
        while size - len(kept[0]) >= 1 << 28:
            size -= len(kept.pop(0))
    return "\n".join(js.trim("".join(kept)).split("\n")[-30:])


def _first_lines(text: str) -> str:
    lines = js.trim(text).split("\n")
    if len(lines) > 40:
        lines[40:] = [f"... {len(lines) - 40} more lines"]
    return "\n".join(lines)


def _stop_of(r: FileResult) -> Stop:
    errors: list[Part] = []
    for m in [] if r.error else Messages(r.output):
        if not isinstance(m, str) and (
            m.level in (LEVEL.ERROR, LEVEL.TLCBUG) or (errors and m.level == LEVEL.STATE)
        ):
            errors.append(m)
    if not errors:
        return Stop(r.status, _tail(r))
    return Stop(r.status, _first_lines("".join(plain_text(errors))))


def _sany_errors(r: FileResult) -> str | None:
    if r.error:
        return None
    text = "".join(plain_text(Messages(r.output)))
    at = _SANY_ERRORS.search(text)
    return None if at is None else _first_lines(text[at.start() :])


def _names(rules: list[Rule], kind: str) -> list[str]:
    return [rule.name for rule in rules if rule.kind == kind]


def _broken_rule(rules: list[Rule], broke: Break) -> Rule | None:
    if broke.kind == "temporal":
        return None
    for rule in rules:
        if rule.kind == broke.kind and (broke.kind == "deadlock" or rule.name == broke.name):
            return rule
    if broke.kind == "invariant":
        for rule in rules:
            if rule.kind == "property" and rule.name == broke.name:
                return rule
    return None


def _only(marks: Iterable[Mark], rules: set[str]) -> Iterator[Mark]:
    for m in marks:
        kept = [name for name in m.broken if name in rules]
        if kept:
            yield Mark(m.values, kept)


def _write(file: str, text: str) -> None:
    with open(file, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def _read(file: str) -> str:
    with open(file, "rb") as f:
        return f.read().decode("utf-8", "replace")


@dataclass(eq=False)
class _Judged:
    first: FileResult
    stop: Stop | None
    states: States
    verdicts: dict[str, Verdict]


def check(spec_file: str, config_file: str) -> CheckResult:
    cfg = read_config(config_file, _read(config_file))
    checks = read_checks(config_file, cfg)
    folder = os.path.dirname(os.path.abspath(spec_file))
    dir_ = tempfile.mkdtemp(prefix="statechart-")
    try:
        tlc = _find_tlc(dir_)

        def config(name: str, sections: list[ConfigSection], extra: list[str]) -> list[str]:
            _write(os.path.join(dir_, f"{name}.cfg"), config_text(sections, extra))
            return [
                "-metadir",
                os.path.join(dir_, f"meta-{name}"),
                "-config",
                os.path.join(dir_, f"{name}.cfg"),
            ]

        env = dict(os.environ) if sys.platform == "darwin" else {**os.environ, "LC_ALL": "C.UTF-8"}

        def run_java(
            name: str, main: str, args: list[str], jvm: list[str] | None = None
        ) -> FileResult:
            tmp = os.path.join(dir_, f"tmp-{name}")
            os.mkdir(tmp)
            return _run_to_files(
                tlc.java,
                [
                    f"-Djava.io.tmpdir={tmp}",
                    f"-DTLA-Library={folder}",
                    "-Dstdout.encoding=UTF-8",
                    "-Dstderr.encoding=UTF-8",
                    *(jvm or []),
                    "-cp",
                    tlc.jar,
                    main,
                    *args,
                ],
                out=os.path.join(dir_, name),
                cwd=dir_,
                env=env,
            )

        xml = run_java(
            "sany",
            "tla2sany.xml.XMLExporter",
            ["-o", "-I", folder, os.path.abspath(spec_file)],
            ["-XX:TieredStopAtLevel=1"],
        )
        if xml.status != 0:
            errors = (
                None
                if xml.error
                else _sany_errors(
                    run_java(
                        "sany-errors",
                        "tla2sany.SANY",
                        [os.path.abspath(spec_file)],
                        ["-XX:TieredStopAtLevel=1"],
                    )
                )
            )
            raise StatechartError(
                f"SANY could not read {spec_file} (exit {js.string(xml.status)}):\n"
                f"{errors if errors is not None else _tail(xml)}"
            )
        sany = read_sany(_read(xml.stdout))
        module = os.path.basename(spec_file)
        module = module[: -len(".tla")] if module.endswith(".tla") else module
        spec = read_spec(module, sany, checks)
        spec.folder = folder
        rules = state_rules(spec)
        all_rules = [*rules, *(Rule("property", name) for name in spec.properties)]

        def eliminate(
            target_rules: list[Rule],
            *,
            prefix: str,
            bound_module: str,
            extra_lines: list[str],
            always_bounded: bool,
            fail_on_unknown_exit: bool,
        ) -> _Judged:
            verdicts: dict[str, Verdict] = {}

            def decide(rule: Rule, outcome: str, r: FileResult | None = None) -> None:
                verdicts[rule_key(rule)] = Verdict(
                    rule, outcome, None if r is None else Messages(r.output)
                )

            groups = [target_rules]
            first: FileResult | None = None
            stop: Stop | None = None
            states = States()
            k = 1
            while groups:
                group = [rule for rule in groups[0] if rule_key(rule) not in verdicts]
                if first is not None and not group:
                    groups.pop(0)
                    continue
                name = f"{prefix}-{k}"
                k += 1
                extra = list(extra_lines)
                invariants = _names(group, "invariant")
                properties = _names(group, "property")
                if invariants:
                    extra.append(f"INVARIANT {' '.join(invariants)}")
                if properties:
                    extra.append(f"PROPERTY {' '.join(properties)}")
                bounded = always_bounded or (first is not None and not states.complete)
                if bounded:
                    extra.append("CONSTRAINT ChartBound")
                r = run_java(
                    name,
                    "tlc2.TLC",
                    [
                        "-tool",
                        *PINNED_FLAGS,
                        *([] if _names(group, "deadlock") else ["-deadlock"]),
                        *config(name, spec.written, extra),
                        bound_module if bounded else spec.module,
                    ],
                )
                if first is None:
                    first = r
                read = read_verdict(Messages(r.output))
                broke = read.broke
                states.distinct = max(states.distinct, read.distinct)
                states.initial = max(states.initial, read.initial)
                rule = _broken_rule(group, broke) if broke else None
                cut = bounded and read.distinct >= RERUN_STATES
                if _exit_class(r.status) == 2:
                    stop = _stop_of(r)
                    break
                if rule:
                    decide(rule, "broken", r)
                elif cut and (r.status == 0 or (broke is not None and broke.kind == "temporal")):
                    states.cut = True
                    for rule in group:
                        decide(rule, "not checked")
                elif r.status == 0:
                    states.complete = True
                    for rule in group:
                        decide(rule, "holds")
                elif broke and properties:
                    if broke.kind == "temporal":
                        states.complete = True
                        for rule in group:
                            if rule.kind != "property":
                                decide(rule, "holds")
                    pending: list[list[Rule]] = []
                    rest: list[Rule] = []
                    for rule in group:
                        if rule.kind == "property":
                            pending.append([rule])
                        elif rule_key(rule) not in verdicts:
                            rest.append(rule)
                    if len(pending) == 1:
                        decide(pending[0][0], "broken", r)
                    else:
                        groups[0:1] = [rest, *pending]
                elif fail_on_unknown_exit:
                    raise StatechartError(
                        f"TLC exited {js.string(r.status)} on {spec_file}, but its output names no "
                        f"rule that broke:\n{_tail(r)}"
                    )
                else:
                    stop = Stop(r.status, _tail(r))
                    break
            for rule in target_rules:
                if rule_key(rule) not in verdicts:
                    decide(rule, "not checked")
            assert first is not None
            return _Judged(first, stop, states, verdicts)

        _write(os.path.join(dir_, "ChartBound.tla"), bound_run(spec.module))
        judged = eliminate(
            all_rules,
            prefix="verdict",
            bound_module="ChartBound",
            extra_lines=[],
            always_bounded=False,
            fail_on_unknown_exit=True,
        )
        verdicts = judged.verdicts
        exit_ = _exit_class(judged.first.status)

        def failed(r: FileResult) -> StatechartError:
            return StatechartError(
                f"TLC could not check {spec_file} (exit {js.string(r.status)}):\n"
                f"{_stop_of(r).message}"
            )

        initial_only = initial_only_properties(sany, spec)

        def properties_with(bug_of: Callable[[Trace], Lasso | None]) -> list[Property]:
            properties: list[Property] = []
            for rule in all_rules:
                if rule.kind != "property":
                    continue
                v = must(verdicts, rule_key(rule))
                bug = (
                    bug_of(read_trace(v.messages)) if v.outcome == "broken" and v.messages else None
                )
                properties.append(
                    Property(v.rule, v.outcome, v.messages, bug, rule.name in initial_only)
                )
            return properties

        if exit_ == 2:
            raise failed(judged.first)
        checked = [must(verdicts, rule_key(rule)) for rule in rules]

        def check_assumptions() -> list[AssumptionCheck]:
            held_rules = [
                rule for rule in all_rules if must(verdicts, rule_key(rule)).outcome == "holds"
            ]
            if not spec.assumptions or not held_rules:
                return []
            _write(
                os.path.join(dir_, "ChartAssume.tla"),
                assume_run(spec.module, {a.arity for a in spec.assumptions}),
            )

            def check_relaxed(
                relaxed: list[Assumption], label: str, target_rules: list[Rule]
            ) -> AssumptionCheck:
                sub = eliminate(
                    target_rules,
                    prefix=f"assume-{label}",
                    bound_module="ChartAssume",
                    extra_lines=[f"CONSTANT {a.name} <- ChartTrue{a.arity}" for a in relaxed],
                    always_bounded=True,
                    fail_on_unknown_exit=False,
                )
                broken = [
                    r.name
                    for r in target_rules
                    if must(sub.verdicts, rule_key(r)).outcome == "broken"
                ]
                not_checked = [
                    r.name
                    for r in target_rules
                    if must(sub.verdicts, rule_key(r)).outcome == "not checked"
                ]
                return AssumptionCheck(
                    [a.name for a in relaxed],
                    broken,
                    not_checked,
                    cut=sub.states.cut,
                    stop=sub.stop,
                )

            out = [check_relaxed([a], a.name, held_rules) for a in spec.assumptions]
            if len(spec.assumptions) >= 2:
                broken_single = {name for ac in out for name in ac.broken}
                remaining = [r for r in held_rules if r.name not in broken_single]
                if remaining:
                    combined = check_relaxed(spec.assumptions, "all", remaining)
                    if combined.broken or combined.not_checked or combined.stop:
                        out.append(combined)
            return out

        assumption_checks = check_assumptions()

        def result(
            graph: Graph,
            paths: list[Bug] | None,
            properties: list[Property],
            drawing: Drawing | None,
        ) -> CheckResult:
            return CheckResult(
                spec=spec,
                graph=graph,
                paths=paths,
                rules=checked,
                properties=properties,
                exit=exit_,
                stop=judged.stop,
                drawing=drawing,
                states=judged.states,
                messages=Messages(judged.first.output),
                assumptions=assumption_checks,
            )

        if judged.states.distinct <= CHART_STATES:
            tag = f"chart-{secrets.token_hex(16)}"
            _write(os.path.join(dir_, "ChartRun.tla"), chart_run(spec, tag))
            drawn = run_java(
                "ChartRun",
                "tlc2.TLC",
                [
                    "-tool",
                    *PINNED_FLAGS,
                    "-deadlock",
                    *config(
                        "ChartRun", spec.written, ["INVARIANT ChartMark", "CONSTRAINT ChartBudget"]
                    ),
                    "-dump",
                    "dot,actionlabels",
                    os.path.join(dir_, "graph"),
                    "ChartRun",
                ],
            )
            file = os.path.join(dir_, "graph.dot")
            if not os.path.exists(file):
                raise failed(drawn)
            if read_verdict(Messages(drawn.output)).distinct <= CHART_STATES:
                graph = parse_dot(file_lines(file))
                find = finder(graph, spec.variables)
                drawing = None if drawn.status == 0 else Drawing(drawn.status)
                broken = {
                    v.rule.name
                    for v in verdicts.values()
                    if v.rule.kind == "invariant" and v.outcome == "broken"
                }
                marks = _only(read_marks(read_messages(file_lines(drawn.stdout)), tag), broken)
                past = mark(graph, marks, spec.variables, rules, find)
                excludes = has_section(spec, "ACTION_CONSTRAINT")
                for rule in rules:
                    v = must(verdicts, rule_key(rule))
                    if (
                        rule.kind == "deadlock"
                        and v.outcome == "broken"
                        and not drawing
                        and not has_section(spec, "CONSTRAINT", "ACTION_CONSTRAINT")
                    ):
                        dead_ends(graph, rule)
                    if v.outcome != "broken" or not v.messages:
                        continue
                    counterexample = read_counterexample(v.messages)
                    seq = [TraceSeqState(t.action, t.vars) for t in counterexample]
                    if not drawing or lasso(graph, Trace(seq, None), spec.variables, find):
                        add_past(graph, counterexample, spec.variables, rule, past, excludes, find)
                properties = properties_with(
                    lambda trace: lasso(graph, trace, spec.variables, find)
                )
                return result(graph, None, properties, drawing)
        drawn_paths = path_graph(spec.variables)
        paths: list[Bug] = []
        for rule in rules:
            v = must(verdicts, rule_key(rule))
            if v.outcome == "broken" and v.messages:
                paths.append(drawn_paths.bug(rule, read_counterexample(v.messages)))
        return result(drawn_paths.graph, paths, properties_with(drawn_paths.lasso), None)
    finally:
        shutil.rmtree(dir_, ignore_errors=True)
