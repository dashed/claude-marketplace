"""Verify delete-comment's scanner: comment kinds, line counts, safe deletion, and the ratchet."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import textwrap
import tokenize
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/delete-comment/skills/delete-comment/scripts/comments.py"

spec = importlib.util.spec_from_file_location("delete_comment_comments", SCRIPT)
assert spec and spec.loader
comments = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = comments
spec.loader.exec_module(comments)


def scan(name: str, source: str) -> Any:
    text = textwrap.dedent(source)
    return comments.scan_text(text, name, comments.find_lexer(name, text), comments.Options())


def kinds(name: str, source: str) -> list[tuple[int, str, str]]:
    return [(item.line, item.kind, item.placement) for item in scan(name, source).items]


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("COV_CORE_", "COVERAGE_"))}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--jobs", "1"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content))


def verdicts(root: Path, category: str = "tautology", **ref: str) -> Path:
    """Write a verdict for every plain item, with the same category and optional ref."""
    records = [json.loads(line) for line in run(root, "inventory").stdout.splitlines()]
    path = root / "verdicts.jsonl"
    lines = [json.dumps({**record, "category": category, **ref}) for record in records]
    path.write_text("\n".join(lines) + "\n")
    return path


def test_python_kinds_keep_tool_comments() -> None:
    found = kinds(
        "a.py",
        '''\
        #!/usr/bin/env python3
        # -*- coding: utf-8 -*-
        # Copyright 2026 Example Corp. MIT License.
        # /// script
        # dependencies = ["pygments"]
        # ///
        # Load the settings.
        # Then cache them.
        """Docstring with # no comment."""
        import os  # noqa: F401
        x = "# not a comment"  # type: ignore[assignment]
        y = 1  # explain why  # noqa: E501
        #: Sphinx reads this attribute comment.
        z = 2
        ''',
    )
    assert found == [
        (1, "directive", "full-line"),
        (2, "directive", "full-line"),
        (3, "license", "full-line"),
        (4, "directive", "full-line"),
        (7, "plain", "full-line"),
        (10, "directive", "trailing"),
        (11, "directive", "trailing"),
        (12, "directive", "trailing"),
        (13, "doc", "full-line"),
    ]
    items = scan("a.py", "y = 1  # explain why  # noqa: E501\n").items
    assert items[0].prose is True


def test_javascript_kinds_ignore_markers_in_strings_and_regexes() -> None:
    found = kinds(
        "a.js",
        """\
        #!/usr/bin/env node
        /* global window */
        // eslint-disable-next-line no-console
        const a = "// no", b = `// no ${a}`, r = /\\/\\//g;
        const c = /* @__PURE__ */ make();
        /** Make a thing. */
        function make() {}
        /** @type {number} */
        let n = 1; // plain trailing
        """,
    )
    assert found == [
        (1, "directive", "full-line"),
        (2, "directive", "full-line"),
        (3, "directive", "full-line"),
        (5, "directive", "inline"),
        (6, "doc", "full-line"),
        (8, "directive", "full-line"),
        (9, "plain", "trailing"),
    ]


@pytest.mark.parametrize(
    ("name", "source", "expected"),
    [
        (
            "a.go",
            "//go:build linux\n\n// F does x.\nfunc F() {}\n\n// loose note\n\nvar v = 1\n",
            [(1, "directive", "full-line"), (3, "doc", "full-line"), (6, "plain", "full-line")],
        ),
        (
            "a.c",
            "#include <stdio.h>\n#define X 1 // trail\n/* block */\nint main(void) { return 0; }\n",
            [(2, "plain", "trailing"), (3, "plain", "full-line")],
        ),
        (
            "a.rs",
            "/// Item doc.\nfn f() {} // trail\n",
            [(1, "doc", "full-line"), (2, "plain", "trailing")],
        ),
        ("a.swift", "/// Doc.\nfunc f() {}\n", [(1, "doc", "full-line")]),
        ("a.hs", "{-# LANGUAGE GADTs #-}\nmodule M where\n", [(1, "directive", "full-line")]),
        (
            "Makefile",
            "# build things\nall: ## Build everything\n\techo hi\n",
            [(1, "plain", "full-line"), (2, "directive", "trailing")],
        ),
        (
            "a.sh",
            "#!/bin/sh\n# shellcheck disable=SC2086\necho $x\n",
            [(1, "directive", "full-line"), (2, "directive", "full-line")],
        ),
    ],
)
def test_other_languages(name: str, source: str, expected: list[tuple[int, str, str]]) -> None:
    assert kinds(name, source) == expected


@pytest.mark.parametrize(
    ("name", "source", "kind"),
    [
        ("a.py", "x = []  # type: list[int]\n", "directive"),
        ("a.ts", "// type: 'module' is required for ES output\nexport {};\n", "plain"),
        ("a.c", "/* fall through */\n", "directive"),
        ("a.py", "# Fall through to the 404 handler.\n", "plain"),
        ("a.ts", "// #region Helpers\n", "directive"),
        ("a.py", "# region Helpers\n", "directive"),
        ("a.py", "# region, so each table is looked up by name.\n", "plain"),
        ("a.rs", "// SAFETY: the pointer is valid for the whole call.\n", "directive"),
        ("a.go", "// SAFETY: callers hold the lock.\n", "plain"),
    ],
)
def test_language_scoped_directives(name: str, source: str, kind: str) -> None:
    assert [item.kind for item in scan(name, source).items] == [kind]


def test_consecutive_comments_group_by_indentation_and_kind() -> None:
    items = scan(
        "a.py",
        """\
        # one
        # two
        def f():
            # three
            # pylint: disable=too-many-locals
            # four
            return 1
        """,
    ).items
    assert [(i.line, i.end_line, i.lines, i.kind) for i in items] == [
        (1, 2, 2, "plain"),
        (4, 4, 1, "plain"),
        (5, 5, 1, "directive"),
        (6, 6, 1, "plain"),
    ]


def test_hints_are_leads_for_classification() -> None:
    items = scan(
        "a.py",
        """\
        # TODO: remove this hack once the API is fixed
        x = 1
        # result = compute(x)
        y = 2
        # ---------- helpers ----------
        """,
    ).items
    assert [item.hints for item in items] == [["todo", "excuse"], ["code"], ["divider"]]


def test_python_line_counts_match_tokenize() -> None:
    source = textwrap.dedent(
        '''\
        """Module doc.

        It has a blank line.
        """
        # full-line comment
        x = """a

        # inside a string
        """  # trailing

        if x:  # another
            # indented
            pass
        '''
    ).replace("\n", "\r\n")
    comment_lines: set[int] = set()
    code_lines: set[int] = set()
    skipped = {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            comment_lines.add(token.start[0])
        elif token.type not in skipped:
            code_lines.update(range(token.start[0], token.end[0] + 1))
    result = comments.scan_text(
        source, "a.py", comments.find_lexer("a.py", source), comments.Options()
    )
    assert result.code_lines == len(code_lines)
    assert sum(item.lines for item in result.items) == len(comment_lines - code_lines)
    assert sum(item.placement == "trailing" for item in result.items) == 2


def test_delete_removes_only_comments(tmp_path: Path) -> None:
    write(
        tmp_path,
        {
            "app.py": """\
            #!/usr/bin/env python3
            # Increment the counter.
            count = 0  # the count
            count += 1  # noqa: E501
            # Return early.

            def f(value):
                # Add one.
                return value + 1  # done
            """,
            "app.js": "foo(/* first */ bar); // call it\n// eslint-disable-next-line\nbaz();\n",
        },
    )
    result = run(tmp_path, "delete", "--verdicts", str(verdicts(tmp_path)))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "deleted 7 items (tautology 7) in 2 files; 3 lines removed" in result.stdout
    assert (tmp_path / "app.py").read_text() == textwrap.dedent(
        """\
        #!/usr/bin/env python3
        count = 0
        count += 1  # noqa: E501

        def f(value):
            return value + 1
        """
    )
    assert (tmp_path / "app.js").read_text() == "foo(bar);\n// eslint-disable-next-line\nbaz();\n"


def test_delete_keeps_crlf_line_endings(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_bytes(b"# drop\r\nx = 1  # drop too\r\ny = 2\r\n")
    assert run(tmp_path, "delete", "--verdicts", str(verdicts(tmp_path))).returncode == 0
    assert (tmp_path / "a.py").read_bytes() == b"x = 1\r\ny = 2\r\n"


@pytest.mark.parametrize(
    ("category", "ref", "deleted"),
    [
        ("excuse", {}, False),
        ("excuse", {"ref": "tbd"}, False),
        ("excuse", {"ref": "https://example.com/issues/7"}, True),
        ("excuse", {"ref": "acme/api#12"}, True),
        ("excuse", {"ref": "ENG-341"}, True),
        ("excuse", {"ref": "docs/adr/0001-retries.md#issue-1"}, True),
        ("decision", {"ref": "docs/adr/0002-missing.md"}, False),
        ("decision", {"ref": "docs/adr/0001-retries.md"}, True),
        ("decision", {"ref": "https://example.com/adr/1"}, True),
        ("keep", {}, False),
    ],
)
def test_delete_requires_a_ref_for_excuses_and_decisions(
    tmp_path: Path, category: str, ref: dict[str, str], deleted: bool
) -> None:
    write(tmp_path, {"a.py": "# Retry twice: the API drops the first call.\nx = 1\n"})
    write(tmp_path, {"docs/adr/0001-retries.md": "# Retries\n"})
    result = run(tmp_path, "delete", "--verdicts", str(verdicts(tmp_path, category, **ref)))
    assert result.returncode == 0, result.stdout
    assert ((tmp_path / "a.py").read_text() == "x = 1\n") is deleted


def test_delete_never_removes_directives_and_reports_stale_ids(tmp_path: Path) -> None:
    write(tmp_path, {"a.py": "import os  # noqa: F401\n# plain\n"})
    record = json.loads(run(tmp_path, "inventory", "--kinds", "directive").stdout)
    gone = {"id": "000000000000", "path": "a.py", "category": "stale"}
    lines = [json.dumps({**record, "category": "tautology"}), json.dumps(gone)]
    (tmp_path / "v.jsonl").write_text("\n".join(lines) + "\n")
    result = run(tmp_path, "delete", "--verdicts", "v.jsonl")
    assert result.returncode == 1
    assert "skipped 1: directive items are never deleted" in result.stdout
    assert "not found: 000000000000 in a.py" in result.stdout
    assert (tmp_path / "a.py").read_text() == "import os  # noqa: F401\n# plain\n"


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    write(tmp_path, {"a.py": "# plain\nx = 1\n"})
    result = run(tmp_path, "delete", "--verdicts", str(verdicts(tmp_path)), "--dry-run")
    assert "would delete 1 items" in result.stdout
    assert (tmp_path / "a.py").read_text() == "# plain\nx = 1\n"


def test_same_code_rejects_a_code_change() -> None:
    lexer = comments.find_lexer("a.py", "")
    assert comments.same_code("x = 1  # c\n", "x = 1\n", lexer) == (True, "")
    assert comments.same_code("x = 1  # c\n", "x = 2\n", lexer)[0] is False
    js = comments.find_lexer("a.js", "")
    assert comments.same_code("a(); // c\n", "a();\n", js) == (True, "")
    assert comments.same_code("a(); // c\n", "b();\n", js)[0] is False


def test_skipped_files(tmp_path: Path) -> None:
    write(
        tmp_path,
        {
            "gen.py": "# Code generated by protoc. DO NOT EDIT.\n# plain\n",
            "README.md": "<!-- a comment -->\n",
            "data.bin": "",
            "vendor/lib.py": "# plain\n",
            "notes.unknownext": "# plain\n",
            "real.py": "# plain\n",
        },
    )
    (tmp_path / "data.bin").write_bytes(b"\0\1\2")
    report = json.loads(run(tmp_path, "estimate", "--json").stdout)
    assert report["files_scanned"] == 1
    assert report["files_skipped"] == {
        "binary": 1,
        "generated": 1,
        "no-lexer": 1,
        "prose-or-data": 1,
    }
    assert report["generated_files"] == ["gen.py"]


def test_estimate_counts_lines_per_kind_and_verdict(tmp_path: Path) -> None:
    write(tmp_path, {"a.py": "# one\n# two\nx = 1  # three\n# Copyright 2026 X\n"})
    report = json.loads(
        run(tmp_path, "estimate", "--json", "--verdicts", str(verdicts(tmp_path, "stale"))).stdout
    )
    assert report["kinds"]["plain"] == {"items": 2, "lines": 2, "trailing_or_inline": 1}
    assert report["kinds"]["license"]["lines"] == 1
    assert report["categories"]["stale"] == {"items": 2, "lines": 2}
    assert report["lines"] == {"total": 4, "code": 1, "blank": 0, "comment_only": 3}


def test_flags_exclude_paths_allow_directives_and_pick_languages(tmp_path: Path) -> None:
    write(
        tmp_path,
        {
            "app/a.py": "x = 1  # keep-fmt: ours\n# plain\n",
            "app/b.ts": "// plain\nexport {};\n",
            "build/gen.py": "# plain\n",
        },
    )
    records = run(
        tmp_path,
        "inventory",
        "--kinds",
        "all",
        "--exclude",
        "build/*",
        "--allow",
        r"keep-fmt:",
        "--language",
        "Python",
    ).stdout.splitlines()
    found = [(r["path"], r["line"], r["kind"]) for r in map(json.loads, records)]
    assert found == [("app/a.py", 1, "directive"), ("app/a.py", 2, "plain")]
    bad = run(tmp_path, "inventory", "--allow", "(")
    assert bad.returncode == 2
    assert "is not a regular expression" in bad.stderr
