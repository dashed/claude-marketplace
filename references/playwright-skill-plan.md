# Playwright Web Browser Skill - Implementation Plan

> Deep investigation and design document for creating a Python/uv-based browser automation skill using Playwright.

## Executive Summary

This document outlines the plan for creating a **Playwright browser automation skill** for the claude-marketplace. The skill will use:

- **Python** as the runtime (not Node.js)
- **uv** for dependency management with PEP 723 inline script metadata
- **Playwright Python** library for browser automation
- **Progressive disclosure** pattern (focused SKILL.md + references/)

## Research Sources Analyzed

| Source | Path | Key Insights |
|--------|------|--------------|
| playwright-skill (Node.js) | `/Users/me/aaa/github/playwright-skill/` | Universal executor pattern, /tmp scripts, API reference structure |
| agent-commands web-browser | `/Users/me/aaa/github/agent-commands/skills/web-browser/` | CDP-based minimal approach, separate tool scripts |
| playwright-python | `/Users/me/aaa/github/playwright-python/` | Sync and async APIs, browser support matrix |
| uv scripts guide | `/Users/me/aaa/github/uv/docs/guides/scripts.md` | PEP 723 inline metadata, shebang support |
| marketplace skills | `/Users/me/aaa/github/claude-marketplace/plugins/` | SKILL.md patterns, references/ structure |

## Design Decisions

### 1. Python + uv vs Node.js

**Decision**: Use Python with uv inline scripts

**Rationale**:
- uv is becoming the standard Python package manager
- PEP 723 inline metadata makes scripts fully self-contained
- No wrapper script needed (unlike Node.js run.js)
- Better for data processing after scraping
- Python is more accessible to users

### 2. Playwright vs CDP (Puppeteer)

**Decision**: Use Playwright (full launch mode), not CDP connect

**Rationale**:
- Self-contained scripts that manage their own browser lifecycle
- No pre-requisites (no need to start browser with --remote-debugging-port)
- Playwright handles browser binary management
- Cross-browser support (Chromium, Firefox, WebKit)

### 3. Sync vs Async API

**Decision**: Use `playwright.sync_api` (synchronous)

**Rationale**:
- Simpler code without async/await
- Sufficient for single-threaded automation tasks
- Easier for Claude to generate correct code
- Lower barrier for users to modify

### 4. Script Architecture

**Decision**: Self-contained scripts with PEP 723 metadata

Each script includes its own dependencies:
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///

from playwright.sync_api import sync_playwright
```

**Benefits**:
- No global installation needed
- Scripts can be run from anywhere
- uv caches dependencies (fast subsequent runs)
- Fully portable

## Skill Architecture

### Directory Structure

```
plugins/playwright/
├── SKILL.md                          # Main skill (200-250 lines)
├── scripts/                          # Executable Python scripts
│   ├── check_setup.py               # Verify browser installation
│   ├── screenshot.py                # Take screenshots
│   ├── navigate.py                  # Navigate and inspect pages
│   ├── fill_form.py                 # Form automation
│   └── evaluate.py                  # Execute JavaScript
└── references/
    ├── api-reference.md             # Playwright Python API quick ref
    ├── selectors.md                 # Selector patterns
    ├── custom-scripts.md            # Guide to writing custom scripts
    └── troubleshooting.md           # Common issues and solutions
```

### SKILL.md Structure

```markdown
---
name: playwright
description: Browser automation with Playwright for Python. Use when testing
  websites, taking screenshots, filling forms, scraping web content, or
  automating browser interactions. Triggers on browser, web testing,
  screenshots, selenium, puppeteer, or playwright.
---

# Playwright Browser Automation

## Overview
[What the skill does - 2-3 sentences]

## Prerequisites
- Python 3.10+
- uv package manager
- Playwright browser binaries

## Setup (First Time Only)
[One-time browser installation command]

## Quick Start
[Simple screenshot example]

## Common Patterns
### Take a Screenshot
### Fill and Submit a Form
### Scrape Page Content
### Execute JavaScript

## Writing Custom Scripts
[Template for custom automation]

## Quick Reference
[Table of common operations]

## Troubleshooting
[Top 3-5 issues]

## Advanced Usage
For comprehensive API documentation, see:
- [references/api-reference.md](references/api-reference.md)
- [references/selectors.md](references/selectors.md)
```

## Script Specifications

### 1. check_setup.py

**Purpose**: Verify Playwright is installed correctly

**Usage**:
```bash
uv run scripts/check_setup.py
```

**Output**:
- Success: Shows installed browsers
- Failure: Provides installation command

**Implementation**:
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///

import subprocess
import sys

def main():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to get browser executable
            chromium_path = p.chromium.executable_path
            print(f"Chromium: {chromium_path}")
            print("Setup complete!")
    except Exception as e:
        print(f"Error: {e}")
        print("\nRun this command to install browser:")
        print("  uv run --with playwright playwright install chromium")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. screenshot.py

**Purpose**: Take a screenshot of a URL

**Usage**:
```bash
uv run scripts/screenshot.py https://example.com
uv run scripts/screenshot.py https://example.com --output /tmp/shot.png
uv run scripts/screenshot.py https://example.com --full-page
uv run scripts/screenshot.py https://example.com --headless
```

**Options**:
| Flag | Description | Default |
|------|-------------|---------|
| `--output`, `-o` | Output path | `/tmp/screenshot-{timestamp}.png` |
| `--full-page` | Capture full page | False |
| `--headless` | Run headless | False |
| `--width` | Viewport width | 1280 |
| `--height` | Viewport height | 720 |

### 3. navigate.py

**Purpose**: Navigate to URL and extract information

**Usage**:
```bash
uv run scripts/navigate.py https://example.com
uv run scripts/navigate.py https://example.com --title
uv run scripts/navigate.py https://example.com --links
uv run scripts/navigate.py https://example.com --text
```

**Output formats**:
- Default: Title and URL
- `--title`: Just the page title
- `--links`: JSON array of links
- `--text`: Full page text content
- `--html`: HTML content

### 4. fill_form.py

**Purpose**: Fill and submit forms

**Usage**:
```bash
# Interactive mode (prompts for each field)
uv run scripts/fill_form.py https://example.com/form

# With field values
uv run scripts/fill_form.py https://example.com/form \
  --field "email=test@example.com" \
  --field "password=secret123" \
  --submit
```

### 5. evaluate.py

**Purpose**: Execute JavaScript in browser context

**Usage**:
```bash
uv run scripts/evaluate.py https://example.com "document.title"
uv run scripts/evaluate.py https://example.com "document.querySelectorAll('a').length"
```

## Custom Script Template

For SKILL.md, include this template:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///
"""
Custom Playwright automation script.
Save to /tmp/my-automation.py and run with: uv run /tmp/my-automation.py
"""

from playwright.sync_api import sync_playwright
import sys

# Configuration
TARGET_URL = "http://localhost:3000"  # Change this
HEADLESS = False  # Set True for background execution

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        try:
            # Navigate
            page.goto(TARGET_URL)
            print(f"Page title: {page.title()}")

            # Your automation here
            # page.click("button")
            # page.fill("input[name='email']", "test@example.com")
            # page.screenshot(path="/tmp/screenshot.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="/tmp/error-screenshot.png")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
```

## References Content

### references/api-reference.md

Key sections to include:
1. Browser launch options
2. Page navigation methods
3. Element selectors (locators)
4. Actions (click, fill, select)
5. Waiting strategies
6. Screenshots and recordings
7. Network interception
8. Device emulation
9. Assertions

### references/selectors.md

Cover:
1. CSS selectors
2. Text selectors
3. XPath selectors
4. Role-based selectors
5. Data-testid attributes
6. Chaining and filtering
7. Best practices

### references/troubleshooting.md

Common issues:
1. "Browser not found" - installation guide
2. "Timeout waiting for element" - waiting strategies
3. "Element not visible" - scrolling, iframes
4. "SSL certificate error" - bypass options
5. "Headless mode issues" - headed debugging

## Setup Requirements

### One-Time Setup

```bash
# Install browser binaries (required once)
uv run --with playwright playwright install chromium

# Optional: Install all browsers
uv run --with playwright playwright install
```

### Per-Script Execution

No additional setup needed. uv automatically:
1. Creates isolated environment
2. Installs dependencies (cached)
3. Runs script

## Marketplace Integration

### marketplace.json Entry

```json
{
  "name": "playwright",
  "version": "1.0.0",
  "source": "./plugins/playwright",
  "description": "Browser automation with Playwright for Python. Use when testing websites, taking screenshots, filling forms, scraping web content, or automating browser interactions. Triggers on browser, web testing, screenshots, or playwright.",
  "author": {
    "name": "Alberto Leal"
  },
  "repository": "https://github.com/dashed/claude-marketplace/tree/master/plugins/playwright",
  "license": "MIT",
  "keywords": [
    "playwright",
    "browser",
    "automation",
    "testing",
    "screenshots",
    "web",
    "scraping"
  ],
  "strict": false,
  "skills": ["./"]
}
```

### Changelog Entry

```markdown
## [Unreleased]

### Added
- playwright skill: Browser automation with Playwright for Python
- playwright skill: Scripts for screenshots, navigation, form filling
- playwright skill: Comprehensive API reference documentation
```

## Implementation Checklist

### Phase 1: Core Skill
- [ ] Create `plugins/playwright/` directory
- [ ] Write `SKILL.md` with frontmatter
- [ ] Create `scripts/check_setup.py`
- [ ] Create `scripts/screenshot.py`
- [ ] Add to marketplace.json
- [ ] Create changelog entry

### Phase 2: Additional Scripts
- [ ] Create `scripts/navigate.py`
- [ ] Create `scripts/fill_form.py`
- [ ] Create `scripts/evaluate.py`

### Phase 3: References
- [ ] Write `references/api-reference.md`
- [ ] Write `references/selectors.md`
- [ ] Write `references/custom-scripts.md`
- [ ] Write `references/troubleshooting.md`

### Phase 4: Validation
- [ ] Run `make validate`
- [ ] Test all scripts manually
- [ ] Verify marketplace.json schema
- [ ] Review SKILL.md length (target: <250 lines)

## Comparison with Existing Skills

| Aspect | playwright-skill (Node.js) | This skill (Python/uv) |
|--------|---------------------------|------------------------|
| Runtime | Node.js | Python 3.10+ |
| Package manager | npm | uv |
| Dependency declaration | package.json | PEP 723 inline |
| Wrapper needed | run.js | No (uv run --script) |
| Setup | npm run setup | uv run --with playwright playwright install |
| Script location | /tmp/*.js | /tmp/*.py |
| API | Playwright Node.js | Playwright Python |
| Async model | Async (required) | Sync (simpler) |
| Dev server detection | Built-in helper | Not included |

## Open Questions

1. **Skill name**: `playwright` vs `web-browser` vs `browser-automation`?
   - Recommendation: `playwright` (clear, matches tool name)

2. **Should we include dev server detection?**
   - The Node.js skill has this feature
   - Could add as optional helper, but adds complexity
   - Recommendation: Defer to v1.1.0

3. **Should scripts be in `scripts/` or `tools/`?**
   - `tools/` matches agent-commands convention
   - `scripts/` matches Python convention
   - Recommendation: `scripts/` (Pythonic)

4. **Support Firefox/WebKit or Chromium only?**
   - Chromium is default and most tested
   - Could add `--browser` flag to scripts
   - Recommendation: Chromium default, optional flag for others

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Browser binary size (~200MB) | High | Medium | Clear documentation, one-time setup |
| uv not installed | Medium | High | Check and provide installation instructions |
| Playwright version conflicts | Low | Medium | Pin version in inline metadata |
| Headless mode differences | Medium | Low | Default to headed mode |

## Next Steps

1. **Approve this plan** - Review design decisions
2. **Create directory structure** - Set up files
3. **Write SKILL.md** - Core documentation
4. **Implement check_setup.py** - Setup verification
5. **Implement screenshot.py** - Most common use case
6. **Add to marketplace** - Integration
7. **Write references** - Progressive disclosure content
8. **Run validation** - Ensure all checks pass

---

## Codex MCP Expert Recommendations

> The following recommendations were gathered from Codex MCP consultation (read-only sandbox mode).

### Key Improvements from Codex

#### 1. Pin Playwright Version

**Recommendation**: Always pin to a specific version to match browser binaries.

```python
# /// script
# dependencies = ["playwright==1.56.0"]
# ///
```

**Current stable version**: `1.56.0` (verified from local playwright-python repo; setup.py shows 1.57.0-beta in development)

#### 2. Shebang Confirmation

**Confirmed**: `#!/usr/bin/env -S uv run --script` is the correct shebang for PEP 723 scripts with uv.

#### 3. Improved check_setup.py

Use `executable_path` for fast browser detection:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Check Playwright browser installation status."""

import sys
from playwright.sync_api import sync_playwright

def main():
    print("Checking Playwright browser installation...\n")

    with sync_playwright() as p:
        browsers = {
            "chromium": p.chromium,
            "firefox": p.firefox,
            "webkit": p.webkit,
        }

        available = {}
        missing = []

        for name, bt in browsers.items():
            try:
                path = bt.executable_path
                available[name] = path
                print(f"✓ {name}: {path}")
            except Exception as e:
                missing.append(name)
                print(f"✗ {name}: missing")

        print()

        if missing:
            print("Install missing browsers with:")
            print(f"  uv run --with playwright playwright install {' '.join(missing)}")
            print("\nOr install with system dependencies:")
            print(f"  uv run --with playwright playwright install --with-deps {' '.join(missing)}")
            return 1

        print("All browsers installed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### 4. Robust Script Template

Updated template with all Codex recommendations:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""
Robust Playwright automation template.
Save to /tmp/my-automation.py and run with: uv run /tmp/my-automation.py <url>
"""

import argparse
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

# Environment configuration
HEADLESS = os.getenv("HEADLESS", "0").lower() in ("1", "true", "yes")
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
TRACE = os.getenv("TRACE", "0").lower() in ("1", "true", "yes")


def parse_viewport(value: str) -> dict | None:
    """Parse viewport string like '1280x720' into dict."""
    if not value:
        return None
    try:
        w, h = value.lower().split("x", 1)
        return {"width": int(w), "height": int(h)}
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Playwright automation")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("-o", "--output", help="Screenshot output path")
    args = parser.parse_args()

    viewport = parse_viewport(os.getenv("VIEWPORT", "1280x720"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        context = browser.new_context(viewport=viewport)

        if TRACE:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = context.new_page()
        page.set_default_timeout(15_000)
        page.set_default_navigation_timeout(30_000)

        try:
            page.goto(args.url, wait_until="networkidle")
            print(f"Title: {page.title()}")
            print(f"URL: {page.url}")

            # Your automation code here
            # page.click("button")
            # page.fill("input[name='email']", "test@example.com")

            if args.output:
                page.screenshot(path=args.output, full_page=True)
                print(f"Screenshot: {args.output}")

            return 0

        except Exception as e:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            error_shot = f"/tmp/error-{ts}.png"
            try:
                page.screenshot(path=error_shot, full_page=True)
                print(f"Error screenshot: {error_shot}", file=sys.stderr)
            except Exception:
                pass
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            if TRACE:
                trace_path = "/tmp/trace.zip"
                context.tracing.stop(path=trace_path)
                print(f"Trace saved: {trace_path}")
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
```

#### 5. Environment Variables Reference

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HEADLESS` | Run browser headless | `0` (headed) | `HEADLESS=1` |
| `SLOW_MO` | Slow down actions (ms) | `0` | `SLOW_MO=250` |
| `VIEWPORT` | Browser viewport | `1280x720` | `VIEWPORT=1920x1080` |
| `TRACE` | Enable tracing | `0` (off) | `TRACE=1` |

#### 6. Docker/CI Configuration

**Recommended base image**: `mcr.microsoft.com/playwright/python:v1.56.0`

**Chromium flags for containers**:
```python
browser = p.chromium.launch(
    headless=True,
    args=[
        "--disable-dev-shm-usage",  # Required for Docker
        "--no-sandbox",              # Only if trusted container
        "--single-process",          # Reduce memory usage
        "--disable-gpu",             # No GPU in containers
    ]
)
```

**Environment variables for containers**:
```bash
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright  # Cache location
XDG_CACHE_HOME=/tmp/.cache               # If default cache is read-only
```

#### 7. Tracing for Debugging

Enable tracing to debug complex automations:

```python
# Start tracing
context.tracing.start(screenshots=True, snapshots=True, sources=True)

# ... your automation ...

# Stop and save trace
context.tracing.stop(path="/tmp/trace.zip")
```

View the trace:
```bash
uv run --with playwright playwright show-trace /tmp/trace.zip
```

#### 8. Common Patterns to Document

**Login with session persistence**:
```python
# Save session after login
context.storage_state(path="/tmp/auth.json")

# Reuse session in new context
context = browser.new_context(storage_state="/tmp/auth.json")
```

**Wait for dynamic content (SPAs)**:
```python
# Wait for network idle
page.goto(url, wait_until="networkidle")

# Wait for specific element
page.locator(".loaded-content").wait_for(state="visible")

# Avoid arbitrary sleeps - use locator waits instead
```

**Handle popups**:
```python
with page.expect_popup() as popup_info:
    page.click("button.open-popup")
popup = popup_info.value
popup.wait_for_load_state()
```

### Modern Locator API (Playwright 1.56.0)

**IMPORTANT**: Use `get_by_*` methods instead of raw CSS selectors. These are the recommended patterns:

```python
# PREFERRED: Semantic locators (accessible, stable)
page.get_by_role("button", name="Submit").click()
page.get_by_label("Email").fill("user@example.com")
page.get_by_placeholder("Search...").fill("query")
page.get_by_text("Welcome back").wait_for()
page.get_by_test_id("submit-btn").click()
page.get_by_alt_text("Company Logo").screenshot()
page.get_by_title("Close dialog").click()

# AVOID: Raw CSS selectors (fragile)
page.locator("button.btn-primary").click()  # Don't use
page.locator("#submit").click()              # Don't use
```

**Locator Combinators** (new in recent versions):
```python
# OR: Match either locator
new_email = page.get_by_role("button", name="New")
dialog = page.get_by_text("Confirm security settings")
new_email.or_(dialog).first.click()

# AND: Match both conditions
button = page.get_by_role("button").and_(page.get_by_title("Subscribe"))
button.click()

# FILTER: Narrow down results
rows = page.locator("tr")
rows.filter(has_text="Active").filter(
    has=page.get_by_role("button", name="Edit")
).first.click()
```

### Clock API (Time Mocking)

New feature for controlling time in tests:

```python
# Install fake timers
page.clock.install(time=datetime.datetime(2024, 12, 10, 8, 0, 0))
page.goto("https://example.com")

# Fast forward time
page.clock.fast_forward(1000)  # 1 second
page.clock.fast_forward("30:00")  # 30 minutes

# Pause at specific time
page.clock.pause_at(datetime.datetime(2024, 12, 10, 10, 0, 0))

# Resume normal time flow
page.clock.resume()
```

### ARIA Snapshots (Accessibility Testing)

Capture and assert accessibility tree structure:

```python
# Get ARIA snapshot
snapshot = page.get_by_role("navigation").aria_snapshot()
print(snapshot)
# Output (YAML format):
# - navigation:
#   - link "Home"
#   - link "About"
#   - link "Contact"

# Assert ARIA snapshot matches expected structure
from playwright.sync_api import expect
expect(page.locator("nav")).to_match_aria_snapshot('''
- navigation:
  - link "Home"
  - link "About"
''')
```

### Security Considerations

1. **Never hardcode credentials** - Use environment variables
2. **Use storage_state for auth** - Avoid re-entering credentials
3. **Be careful with cookies** - Don't share auth files across environments
4. **Set accept_downloads=False** unless explicitly needed

### Cross-Platform Notes

| Platform | Notes |
|----------|-------|
| macOS | Works out of the box |
| Linux | May need `--with-deps` for system libraries |
| Windows | Path handling differs; use `Path` from pathlib |

### Updated Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Browser binary size (~200MB) | High | Medium | Document one-time setup, cache in CI |
| uv not installed | Medium | High | Check and provide installation instructions |
| Playwright version mismatch | Medium | Medium | **Pin version in inline metadata** |
| Container memory issues | Medium | Medium | **Use --disable-dev-shm-usage flag** |
| Headless mode differences | Low | Low | Default to headed, env toggle for CI |

---

*Document created: 2025-12-06*
*Updated: 2025-12-06 with Codex MCP recommendations*
*Based on investigation of existing skills and tools*
