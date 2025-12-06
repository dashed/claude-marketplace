#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Execute JavaScript in browser context."""

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
        description="Execute JavaScript in browser context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  evaluate.py https://example.com "document.title"
  evaluate.py https://example.com "document.querySelectorAll('a').length"
  evaluate.py https://example.com "JSON.stringify(performance.timing)"
  evaluate.py https://example.com --file /tmp/script.js

JavaScript context:
  The script runs in the page context with access to DOM, window, etc.
  Return values are serialized to JSON when possible.

Environment variables:
  HEADLESS=1    Run browser in headless mode
  SLOW_MO=250   Slow down actions by 250ms
""",
    )
    parser.add_argument("url", help="URL to navigate to")
    parser.add_argument("expression", nargs="?", help="JavaScript expression to evaluate")
    parser.add_argument("--file", "-f", help="Path to JavaScript file to execute")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument(
        "--raw", action="store_true", help="Output raw value without JSON formatting"
    )
    args = parser.parse_args()

    if not args.expression and not args.file:
        parser.error("Either expression or --file is required")

    if args.file:
        try:
            with open(args.file) as f:
                script = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 1
    else:
        script = args.expression

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

            result = page.evaluate(script)

            if args.raw:
                print(result)
            elif result is None:
                print("null")
            elif isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2))
            elif isinstance(result, bool):
                print("true" if result else "false")
            elif isinstance(result, (int, float)):
                print(result)
            else:
                print(result)

            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
