---
name: playwright
description: Browser automation with Playwright for Python. Use when testing websites, taking screenshots, filling forms, scraping web content, or automating browser interactions. Triggers on browser, web testing, screenshots, selenium, puppeteer, or playwright.
---

# Playwright Browser Automation

## Overview

Playwright enables browser automation for web testing, screenshots, form filling, and scraping. This skill uses Python with `uv` for self-contained scripts that require no global installation.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Playwright browser binaries (one-time setup)

## Setup (First Time Only)

> **Claude: Do not run browser installation commands directly.** Suggest these commands to the user and let them run manually. This is a one-time setup that downloads ~200MB of browser binaries.

Suggest the user run:

```bash
# Install Chromium (recommended, ~200MB)
uv run --with playwright playwright install chromium

# Or install all browsers
uv run --with playwright playwright install
```

To verify installation:
```bash
uv run /path/to/plugins/playwright/scripts/check_setup.py
```

## Quick Start

Take a screenshot of any URL:

```bash
uv run /path/to/plugins/playwright/scripts/screenshot.py https://example.com
```

Output: `/tmp/screenshot-{timestamp}.png`

## Common Patterns

### Take a Screenshot

```bash
# Default (visible browser)
uv run scripts/screenshot.py https://example.com

# Full page, headless
uv run scripts/screenshot.py https://example.com --full-page --headless

# Custom output path
uv run scripts/screenshot.py https://example.com -o /tmp/my-shot.png
```

### Navigate and Extract Content

```bash
# Get page title and URL
uv run scripts/navigate.py https://example.com

# Extract all links as JSON
uv run scripts/navigate.py https://example.com --links

# Get page text content
uv run scripts/navigate.py https://example.com --text
```

### Fill and Submit Forms

```bash
uv run scripts/fill_form.py https://example.com/login \
  --field "email=test@example.com" \
  --field "password=secret123" \
  --submit
```

### Execute JavaScript

```bash
uv run scripts/evaluate.py https://example.com "document.title"
uv run scripts/evaluate.py https://example.com "document.querySelectorAll('a').length"
```

## Writing Custom Scripts

Save this template to `/tmp/my-automation.py`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Custom Playwright automation script."""

import os
import sys
from playwright.sync_api import sync_playwright

HEADLESS = os.getenv("HEADLESS", "0").lower() in ("1", "true", "yes")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        try:
            page.goto("https://example.com")
            print(f"Title: {page.title()}")

            # Use semantic locators (preferred)
            page.get_by_role("button", name="Submit").click()
            page.get_by_label("Email").fill("test@example.com")

            # Screenshot
            page.screenshot(path="/tmp/result.png")

        except Exception as e:
            page.screenshot(path="/tmp/error.png")
            print(f"Error: {e}", file=sys.stderr)
            return 1
        finally:
            browser.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Run with:
```bash
uv run /tmp/my-automation.py
```

## Modern Locator API

**Prefer semantic locators over CSS selectors:**

```python
# PREFERRED: Semantic locators (accessible, stable)
page.get_by_role("button", name="Submit").click()
page.get_by_label("Email").fill("user@example.com")
page.get_by_placeholder("Search...").fill("query")
page.get_by_text("Welcome back").wait_for()
page.get_by_test_id("submit-btn").click()

# AVOID: Raw CSS selectors (fragile)
page.locator("button.btn-primary").click()  # Don't use
```

**Combine locators:**

```python
# OR: Match either
page.get_by_role("button", name="New").or_(
    page.get_by_text("Create")
).click()

# Filter: Narrow down
page.locator("tr").filter(has_text="Active").first.click()
```

## Quick Reference

| Operation | Code |
|-----------|------|
| Navigate | `page.goto("https://url")` |
| Click | `page.get_by_role("button", name="X").click()` |
| Fill input | `page.get_by_label("Email").fill("value")` |
| Get text | `page.get_by_role("heading").text_content()` |
| Screenshot | `page.screenshot(path="/tmp/shot.png")` |
| Wait | `page.get_by_text("Loaded").wait_for()` |
| Evaluate JS | `page.evaluate("document.title")` |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HEADLESS` | Run browser headless | `0` (headed) |
| `SLOW_MO` | Slow down actions (ms) | `0` |
| `VIEWPORT` | Browser viewport | `1280x720` |
| `TRACE` | Enable tracing | `0` (off) |

Example:
```bash
HEADLESS=1 SLOW_MO=250 uv run scripts/screenshot.py https://example.com
```

## Tracing for Debugging

Enable tracing to debug complex automations:

```python
context.tracing.start(screenshots=True, snapshots=True, sources=True)
# ... your automation ...
context.tracing.stop(path="/tmp/trace.zip")
```

View the trace:
```bash
uv run --with playwright playwright show-trace /tmp/trace.zip
```

## Troubleshooting

### "Browser not found"

Suggest the user install browser binaries (do not run directly):
```bash
uv run --with playwright playwright install chromium
```

### "Timeout waiting for element"

Use proper waiting strategies:
```python
# Wait for element to be visible
page.get_by_text("Loaded").wait_for(state="visible")

# Wait for network idle
page.goto(url, wait_until="networkidle")
```

### "Element not interactable"

Ensure element is visible and scroll into view:
```python
element = page.get_by_role("button", name="Submit")
element.scroll_into_view_if_needed()
element.click()
```

### Headless mode issues

Debug with headed mode:
```bash
HEADLESS=0 uv run scripts/screenshot.py https://example.com
```

### Container/CI Issues

Use these Chromium flags:
```python
browser = p.chromium.launch(
    headless=True,
    args=["--disable-dev-shm-usage", "--no-sandbox"]
)
```

## Advanced Usage

For comprehensive documentation, see:
- [references/api-reference.md](references/api-reference.md) - Full API reference
- [references/selectors.md](references/selectors.md) - Selector patterns
- [references/custom-scripts.md](references/custom-scripts.md) - Script templates
- [references/troubleshooting.md](references/troubleshooting.md) - Common issues
