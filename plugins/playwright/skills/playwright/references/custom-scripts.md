# Custom Playwright Scripts Guide

How to write custom automation scripts using the Playwright skill.

## Script Template

Save this template to `/tmp/my-automation.py`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""
Custom Playwright automation script.
Run with: uv run /tmp/my-automation.py
"""

import argparse
import os
import sys
from datetime import datetime

from playwright.sync_api import sync_playwright

# Configuration from environment
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
    parser = argparse.ArgumentParser(description="My automation script")
    parser.add_argument("--url", default="https://example.com", help="Target URL")
    parser.add_argument("-o", "--output", help="Screenshot output path")
    args = parser.parse_args()

    viewport = parse_viewport(os.getenv("VIEWPORT", "")) or {"width": 1280, "height": 720}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        context = browser.new_context(viewport=viewport)

        if TRACE:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = context.new_page()
        page.set_default_timeout(15_000)
        page.set_default_navigation_timeout(30_000)

        try:
            # ========================================
            # YOUR AUTOMATION CODE HERE
            # ========================================

            page.goto(args.url, wait_until="networkidle")
            print(f"Title: {page.title()}")

            # Example: Click a button
            # page.get_by_role("button", name="Submit").click()

            # Example: Fill a form
            # page.get_by_label("Email").fill("test@example.com")

            # Example: Extract data
            # links = page.locator("a").all_text_contents()
            # print(links)

            # ========================================

            if args.output:
                page.screenshot(path=args.output, full_page=True)
                print(f"Screenshot: {args.output}")

            return 0

        except Exception as e:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            error_shot = f"/tmp/error-{ts}.png"
            try:
                page.screenshot(path=error_shot)
                print(f"Error screenshot: {error_shot}", file=sys.stderr)
            except Exception:
                pass
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            if TRACE:
                trace_path = "/tmp/trace.zip"
                context.tracing.stop(path=trace_path)
                print(f"Trace: {trace_path}")
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
```

## Running Scripts

```bash
# Basic run
uv run /tmp/my-automation.py

# With arguments
uv run /tmp/my-automation.py --url https://example.com

# With environment variables
HEADLESS=1 uv run /tmp/my-automation.py
SLOW_MO=500 uv run /tmp/my-automation.py
TRACE=1 uv run /tmp/my-automation.py
```

## Common Patterns

### Login Script

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Login and save session state."""

import os
import sys
from playwright.sync_api import sync_playwright

def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://example.com/login")

            # Fill login form
            page.get_by_label("Email").fill(os.environ["EMAIL"])
            page.get_by_label("Password").fill(os.environ["PASSWORD"])
            page.get_by_role("button", name="Sign in").click()

            # Wait for successful login
            page.wait_for_url("**/dashboard")
            print("Login successful!")

            # Save session for reuse
            context.storage_state(path="/tmp/auth.json")
            print("Session saved to /tmp/auth.json")

            return 0

        except Exception as e:
            page.screenshot(path="/tmp/login-error.png")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
```

Run with:
```bash
EMAIL=user@example.com PASSWORD=secret uv run /tmp/login.py
```

### Scraping Script

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Scrape product data from a website."""

import json
import sys
from playwright.sync_api import sync_playwright

def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("https://example.com/products")
            page.wait_for_selector(".product-card")

            # Extract product data
            products = page.evaluate("""
                () => Array.from(document.querySelectorAll('.product-card')).map(card => ({
                    name: card.querySelector('.name')?.textContent?.trim(),
                    price: card.querySelector('.price')?.textContent?.trim(),
                    url: card.querySelector('a')?.href
                }))
            """)

            print(json.dumps(products, indent=2))
            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
```

### Form Submission with Wait

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Submit a form and wait for response."""

import sys
from playwright.sync_api import sync_playwright

def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            page.goto("https://example.com/contact")

            # Fill form
            page.get_by_label("Name").fill("John Doe")
            page.get_by_label("Email").fill("john@example.com")
            page.get_by_label("Message").fill("Hello, this is a test message.")

            # Submit and wait for response
            with page.expect_navigation():
                page.get_by_role("button", name="Send").click()

            # Check for success message
            if page.get_by_text("Thank you").is_visible():
                print("Form submitted successfully!")
                return 0
            else:
                print("Submission may have failed")
                page.screenshot(path="/tmp/form-result.png")
                return 1

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
```

### Multi-Page Navigation

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Navigate through multiple pages and collect data."""

import json
import sys
from playwright.sync_api import sync_playwright

def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        all_items = []

        try:
            page.goto("https://example.com/items")

            while True:
                # Wait for items to load
                page.wait_for_selector(".item")

                # Extract items from current page
                items = page.locator(".item").all_text_contents()
                all_items.extend(items)
                print(f"Collected {len(items)} items from page")

                # Check for next page
                next_btn = page.get_by_role("link", name="Next")
                if next_btn.count() == 0 or not next_btn.is_enabled():
                    break

                next_btn.click()
                page.wait_for_load_state("networkidle")

            print(f"\nTotal items: {len(all_items)}")
            print(json.dumps(all_items, indent=2))
            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
```

### Screenshot with Auth

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Take authenticated screenshot using saved session."""

import sys
from playwright.sync_api import sync_playwright

def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Reuse saved auth state
        context = browser.new_context(storage_state="/tmp/auth.json")
        page = context.new_page()

        try:
            page.goto("https://example.com/dashboard")
            page.wait_for_load_state("networkidle")

            page.screenshot(path="/tmp/dashboard.png", full_page=True)
            print("Screenshot saved to /tmp/dashboard.png")
            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
```

## Adding Dependencies

Add Python packages to the script metadata:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "playwright==1.56.0",
#     "pandas",
#     "beautifulsoup4",
# ]
# ///

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
```

## Debugging Tips

### Enable tracing

```bash
TRACE=1 uv run /tmp/my-script.py
uv run --with playwright playwright show-trace /tmp/trace.zip
```

### Use headed mode with slow-mo

```bash
HEADLESS=0 SLOW_MO=500 uv run /tmp/my-script.py
```

### Add page.pause() for debugging

```python
page.goto("https://example.com")
page.pause()  # Opens Playwright Inspector
page.get_by_role("button", name="Submit").click()
```

### Screenshot on error

```python
try:
    # automation code
except Exception as e:
    page.screenshot(path="/tmp/error.png")
    raise
```

## CI/Docker Configuration

For running in containers:

```python
browser = p.chromium.launch(
    headless=True,
    args=[
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
    ]
)
```

Environment variables for containers:
```bash
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
XDG_CACHE_HOME=/tmp/.cache
```
