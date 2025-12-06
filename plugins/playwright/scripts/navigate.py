#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Navigate to URL and extract information."""

import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

HEADLESS = os.getenv("HEADLESS", "0").lower() in ("1", "true", "yes")
SLOW_MO = int(os.getenv("SLOW_MO", "0"))


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
    parser = argparse.ArgumentParser(
        description="Navigate to URL and extract information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  navigate.py https://example.com           # Show title and URL
  navigate.py https://example.com --title   # Just the title
  navigate.py https://example.com --links   # All links as JSON
  navigate.py https://example.com --text    # Page text content
  navigate.py https://example.com --html    # Page HTML

Environment variables:
  HEADLESS=1    Run browser in headless mode
  SLOW_MO=250   Slow down actions by 250ms
""",
    )
    parser.add_argument("url", help="URL to navigate to")
    parser.add_argument("--title", action="store_true", help="Output only the page title")
    parser.add_argument("--links", action="store_true", help="Output all links as JSON")
    parser.add_argument("--text", action="store_true", help="Output page text content")
    parser.add_argument("--html", action="store_true", help="Output page HTML")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    headless = HEADLESS or args.headless
    viewport = parse_viewport(os.getenv("VIEWPORT", "")) or {"width": 1280, "height": 720}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=SLOW_MO)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        page.set_default_timeout(30_000)
        page.set_default_navigation_timeout(60_000)

        try:
            page.goto(args.url, wait_until="networkidle")

            if args.title:
                print(page.title())
            elif args.links:
                links = page.evaluate("""
                    () => Array.from(document.querySelectorAll('a')).map(a => ({
                        text: a.textContent?.trim() || '',
                        href: a.href
                    })).filter(l => l.href)
                """)
                print(json.dumps(links, indent=2))
            elif args.text:
                text = page.evaluate("() => document.body.innerText")
                print(text)
            elif args.html:
                html = page.content()
                print(html)
            else:
                print(f"Title: {page.title()}")
                print(f"URL: {page.url}")

            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
