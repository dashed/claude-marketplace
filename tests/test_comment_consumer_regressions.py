"""Check concrete documentation consumers without importing fixture modules.

The Sphinx case checks its retained directive and the docstring it consumes,
not a complete Sphinx build. Doctest executes only a verified, fixed call in a
benign namespace; fixture implementations and networking are never executed.
"""

from __future__ import annotations

import ast
import doctest
import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE = Path(__file__).parent / "fixtures/comment-slop-jev-holdout.json"


def case_state(name: str) -> dict[str, Any]:
    cases = json.loads(FIXTURE.read_text())["cases"]
    return next(case["state"] for case in cases if case["name"] == name)


def source_text(state: dict[str, Any], path: str | None = None) -> str:
    path = path or state["candidate"]["path"]
    return next(source["content"] for source in state["sources"] if source["path"] == path)


def proposed_source(state: dict[str, Any]) -> str:
    candidate = state["candidate"]
    lines = source_text(state).splitlines(keepends=True)
    start, end = candidate["start_line"] - 1, candidate["end_line"]
    selected = "".join(lines[start:end])
    assert selected.count(candidate["text"]) == 1
    return (
        "".join(lines[:start])
        + selected.replace(candidate["text"], state["proposal"]["replacement"], 1)
        + "".join(lines[end:])
    )


def function_node(source: str, name: str) -> ast.FunctionDef:
    functions = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(functions) == 1
    return functions[0]


def test_empty_replacement_removes_the_published_autofunction_description() -> None:
    state = case_state("frame_measurement_b")
    assert ".. autofunction:: frames.frame_count" in source_text(state, "docs/frames.rst")
    original = function_node(source_text(state), "frame_count")
    edited = function_node(proposed_source(state), "frame_count")

    assert ast.get_docstring(original) == "Return the number of frames in the clip."
    assert ast.get_docstring(edited) is None
    # The directive remains, but the function description it imports is gone.
    assert ast.dump(original.body[-1]) == ast.dump(edited.body[-1])


def test_empty_replacement_blanks_runtime_help_despite_unchanged_function_body() -> None:
    state = case_state("frame_measurement_c")
    helper = function_node(source_text(state, "help_panel.py"), "frame_count_help")
    expected_return = ast.parse('return frame_count.__doc__ or ""').body[0]
    assert len(helper.body) == 1
    assert ast.dump(helper.body[0]) == ast.dump(expected_return)

    def benign_frame_count() -> int:
        return 0

    def fixed_help_consumer() -> str:
        return benign_frame_count.__doc__ or ""

    benign_frame_count.__doc__ = ast.get_docstring(function_node(source_text(state), "frame_count"))
    assert fixed_help_consumer() == "Return the number of frames in the clip."
    benign_frame_count.__doc__ = ast.get_docstring(
        function_node(proposed_source(state), "frame_count")
    )
    assert fixed_help_consumer() == ""


def banner_doctest(source: str) -> tuple[doctest.TestResults, str]:
    function = function_node(source, "interpreter_banner")
    # Confirm the fixture really returns the string shape used by this namespace.
    expected_return = ast.parse('return f"Python {platform.python_version()}"').body[0]
    assert len(function.body) == 2
    assert ast.dump(function.body[-1]) == ast.dump(expected_return)
    assert isinstance(ast.parse(source).body[0], ast.Import)
    assert ast.dump(ast.parse(source).body[0]) == ast.dump(ast.parse("import platform").body[0])
    docstring = ast.get_docstring(function)
    assert docstring is not None

    def interpreter_banner() -> str:
        return "Python 3.12.9"

    example_test = doctest.DocTestParser().get_doctest(
        docstring,
        {"interpreter_banner": interpreter_banner},
        "banner",
        "banner.py",
        0,
    )
    assert len(example_test.examples) == 1
    example = example_test.examples[0]
    # Reject arbitrary fixture examples before the runner can execute them.
    assert ast.dump(ast.parse(example.source)) == ast.dump(ast.parse("interpreter_banner()"))
    assert example.want == "'Python ...'\n"
    assert set(example.options) <= {doctest.ELLIPSIS}
    output: list[str] = []
    result = doctest.DocTestRunner(verbose=False).run(example_test, out=output.append)
    return result, "".join(output)


@pytest.mark.parametrize(
    ("name", "expected_failures"),
    [("interpreter_example_a", 0), ("interpreter_example_b", 1)],
)
def test_doctest_reduction_preserves_the_execution_directive(
    name: str, expected_failures: int
) -> None:
    state = case_state(name)
    consumer = source_text(state, "tests/test_banner_examples.py")
    assert "doctest.testmod(banner)" in consumer
    assert "assert attempted == 1" in consumer
    original, original_output = banner_doctest(source_text(state))
    assert original == doctest.TestResults(failed=0, attempted=1)
    assert original_output == ""

    proposed, failure_output = banner_doctest(proposed_source(state))
    assert proposed == doctest.TestResults(failed=expected_failures, attempted=1)
    if expected_failures:
        assert "Expected:" in failure_output
        assert "'Python ...'" in failure_output
        assert "Got:" in failure_output
        assert "'Python 3.12.9'" in failure_output
    else:
        assert failure_output == ""


def test_removing_the_false_allowlist_claim_matches_the_implementation() -> None:
    state = case_state("resolver_boundary")
    resolver = function_node(source_text(state), "resolve_addresses")
    expected_resolution = ast.parse(
        "return [item[4][0] for item in socket.getaddrinfo(hostname, None)]"
    ).body[0]
    assert len(resolver.body) == 2
    assert [argument.arg for argument in resolver.args.args] == ["hostname"]
    assert ast.dump(resolver.body[-1]) == ast.dump(expected_resolution)

    caller = function_node(source_text(state, "client.py"), "allowed_addresses")
    expected_filter = ast.parse(
        "return [address for address in resolve_addresses(hostname) if address in allowlist]"
    ).body[0]
    assert len(caller.body) == 1
    assert ast.dump(caller.body[0]) == ast.dump(expected_filter)

    # Filtering belongs to the caller; the resolver returns every resolved address.
    original_doc = ast.get_docstring(resolver)
    assert original_doc is not None
    assert "Every returned address has already passed the caller's allowlist." in original_doc
    edited = function_node(proposed_source(state), "resolve_addresses")
    assert ast.get_docstring(edited) == (
        "Resolve the hostname to numeric addresses without allowlist filtering."
    )
    assert ast.dump(edited.body[-1]) == ast.dump(expected_resolution)
