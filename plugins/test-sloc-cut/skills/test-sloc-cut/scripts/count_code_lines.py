#!/usr/bin/env python3
"""Count total, code, comment-only lines and tests per file, with the tokenizer.

Usage:
    python3 count_code_lines.py test_a.py test_b.py ...

Prints one row per file and a code-line total. Run it once at the baseline
commit and once after the cut; the report compares the two.

"Code" is any line that carries a token other than a comment, newline,
indent or dedent. Docstrings count as code on purpose: they are lines a
reader has to read. A trailing comment on a code line does not make it a
comment line. `grep -v '^#'` gets both of those wrong, and misclassifies
every line inside a multi-line string.

"Tests" counts lines that start with `def test_` after stripping leading
whitespace -- module-level pytest functions and unittest methods alike.
Parametrized tests count once; the report should say so.
"""
import io
import sys
import tokenize

SKIP = {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
        tokenize.ENDMARKER, tokenize.ENCODING}


def count(path):
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines()
    comment, code = set(), set()
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            comment.add(tok.start[0])
        elif tok.type not in SKIP:
            code.update(range(tok.start[0], tok.end[0] + 1))
    tests = sum(1 for line in lines if line.lstrip().startswith("def test_"))
    return len(lines), len(code), len(comment - code), tests


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    total = 0
    for path in argv[1:]:
        n_lines, n_code, n_comment, n_tests = count(path)
        print(f"{n_lines:5d} total {n_code:5d} code {n_comment:4d} comment-only {n_tests:4d} tests  {path}")
        total += n_code
    print("code total", total)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
