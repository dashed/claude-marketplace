#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Take a screenshot of a URL."""

import argparse
import os
import sys
from datetime import datetime

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
        description="Take a screenshot of a URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  screenshot.py https://example.com
  screenshot.py https://example.com --output /tmp/shot.png
  screenshot.py https://example.com --full-page --headless
  screenshot.py https://example.com --width 1920 --height 1080

Environment variables:
  HEADLESS=1    Run browser in headless mode
  SLOW_MO=250   Slow down actions by 250ms
  VIEWPORT=1920x1080  Set viewport size
""",
    )
    parser.add_argument("url", help="URL to screenshot")
    parser.add_argument(
        "-o", "--output", help="Output path (default: /tmp/screenshot-{timestamp}.png)"
    )
    parser.add_argument("--full-page", action="store_true", help="Capture full page")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--width", type=int, default=1280, help="Viewport width (default: 1280)")
    parser.add_argument("--height", type=int, default=720, help="Viewport height (default: 720)")
    args = parser.parse_args()

    headless = HEADLESS or args.headless
    viewport = parse_viewport(os.getenv("VIEWPORT", "")) or {
        "width": args.width,
        "height": args.height,
    }

    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = f"/tmp/screenshot-{timestamp}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=SLOW_MO)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        page.set_default_timeout(30_000)
        page.set_default_navigation_timeout(60_000)

        try:
            page.goto(args.url, wait_until="networkidle")
            page.screenshot(path=output_path, full_page=args.full_page)
            print(output_path)
            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            # Try to capture error screenshot
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            error_path = f"/tmp/error-{ts}.png"
            try:
                page.screenshot(path=error_path)
                print(f"Error screenshot: {error_path}", file=sys.stderr)
            except Exception:
                pass
            return 1

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
