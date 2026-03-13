"""Shared fixtures for react-best-practices tests."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture
def sample_rule_md() -> str:
    """A complete rule markdown string with frontmatter, examples, and references."""
    return dedent("""\
        ---
        title: Promise.all() for Independent Operations
        impact: CRITICAL
        impactDescription: 2-10x improvement
        tags: async, parallelization, promises
        ---

        ## Promise.all() for Independent Operations

        When async operations have no interdependencies, execute them concurrently.

        **Incorrect (sequential execution, 3 round trips):**

        ```typescript
        const user = await fetchUser()
        const posts = await fetchPosts()
        const comments = await fetchComments()
        ```

        **Correct (parallel execution, 1 round trip):**

        ```typescript
        const [user, posts, comments] = await Promise.all([
          fetchUser(),
          fetchPosts(),
          fetchComments()
        ])
        ```

        Reference: [React Docs](https://react.dev)
    """)


@pytest.fixture
def sample_rule_no_frontmatter() -> str:
    """A rule markdown string without frontmatter."""
    return dedent("""\
        ## Use Memo for Expensive Calculations

        **Impact: HIGH (significant CPU savings)**

        Memoize expensive computations to avoid recalculating on every render.

        **Incorrect (recalculates every render):**

        ```typescript
        const sorted = expensiveSort(items)
        ```

        **Correct (memoized):**

        ```typescript
        const sorted = useMemo(() => expensiveSort(items), [items])
        ```
    """)


@pytest.fixture
def sample_rule_minimal() -> str:
    """A minimal valid rule with just title, explanation, and examples."""
    return dedent("""\
        ## Minimal Rule

        This is the explanation.

        **Incorrect:**

        ```typescript
        bad()
        ```

        **Correct:**

        ```typescript
        good()
        ```
    """)


@pytest.fixture
def sample_rule_tsx() -> str:
    """A rule with tsx code blocks."""
    return dedent("""\
        ---
        title: Use Key Prop Correctly
        impact: MEDIUM
        tags: rendering, keys
        ---

        ## Use Key Prop Correctly

        Always use stable, unique keys for list items.

        **Incorrect (using index as key):**

        ```tsx
        {items.map((item, i) => <Item key={i} />)}
        ```

        **Correct (using stable ID):**

        ```tsx
        {items.map(item => <Item key={item.id} />)}
        ```
    """)


@pytest.fixture
def sample_rule_multiple_code_blocks() -> str:
    """A rule with multiple code blocks per example and additional text."""
    return dedent("""\
        ---
        title: Avoid Nested Awaits
        impact: HIGH
        ---

        ## Avoid Nested Awaits

        Do not nest await calls unnecessarily.

        **Incorrect (nested awaits):**

        ```typescript
        const result = await fetch(await getUrl())
        ```

        This creates a waterfall of sequential requests.

        **Correct (separated awaits):**

        ```typescript
        const url = await getUrl()
        const result = await fetch(url)
        ```

        This makes the dependency chain explicit.
    """)


@pytest.fixture
def sample_sections_md() -> str:
    """A sample _sections.md content."""
    return dedent("""\
        # Sections

        ---

        ## 1. Eliminating Waterfalls (async)

        **Impact:** CRITICAL
        **Description:** Waterfalls are the #1 performance killer.

        ## 2. Bundle Size Optimization (bundle)

        **Impact:** HIGH
        **Description:** Reducing initial bundle size improves TTI and LCP.
    """)


@pytest.fixture
def rules_dir(tmp_path: Path, sample_rule_md: str, sample_sections_md: str) -> Path:
    """Create a temporary rules directory with sample rule files."""
    rules = tmp_path / "rules"
    rules.mkdir()

    # Write a sample rule
    (rules / "async-parallel.md").write_text(sample_rule_md, encoding="utf-8")

    # Write sections file
    (rules / "_sections.md").write_text(sample_sections_md, encoding="utf-8")

    return rules


@pytest.fixture
def metadata_file(tmp_path: Path) -> Path:
    """Create a sample metadata.json file."""
    import json

    metadata = {
        "version": "1.0.0",
        "organization": "Engineering",
        "date": "March 2026",
        "abstract": "Performance optimization guide.",
        "references": ["https://react.dev", "https://nextjs.org"],
    }
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path
