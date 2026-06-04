"""Pytest configuration for the bundled fuzzy-search test suite.

The test module is copied **verbatim** from the upstream mcp-personal repo,
where the server script lives at the repo root and is launched in the CLI
tests as a bare filename:

    subprocess.run([sys.executable, "mcp_fuzzy_search.py", ...])

In this plugin the server lives under ``scripts/`` instead of the repo root,
so that bare relative invocation would not resolve from pytest's working
directory. Rather than editing the verbatim test body, this autouse fixture
changes the working directory to the ``scripts/`` directory for the duration
of each test, so the bare ``mcp_fuzzy_search.py`` filename resolves correctly.

This is safe because:
  * Every test that touches the real filesystem uses absolute ``tmp_path``
    paths, so a different cwd does not change their behavior.
  * The only tests that pass a relative ``"."`` path
    (``test_cli_content_only_flag`` / ``test_multiline_cli_support``) mock the
    underlying search functions, so ``"."`` is never actually walked.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# .../plugins/fuzzy-search/scripts (sibling of this tests/ directory)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture(autouse=True)
def _chdir_to_scripts():
    """Run each test with cwd set to scripts/ so the bare
    ``mcp_fuzzy_search.py`` subprocess invocation resolves."""
    prev = os.getcwd()
    os.chdir(_SCRIPTS_DIR)
    try:
        yield
    finally:
        os.chdir(prev)
