#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Fill and submit forms."""

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


def parse_field(field: str) -> tuple[str, str]:
    """Parse field string like 'name=value' into tuple."""
    if "=" not in field:
        raise ValueError(f"Invalid field format: {field}. Use 'name=value'")
    name, value = field.split("=", 1)
    return name.strip(), value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fill and submit forms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fill_form.py https://example.com/login \\
    --field "email=test@example.com" \\
    --field "password=secret123" \\
    --submit

  fill_form.py https://example.com/search \\
    --field "q=search query" \\
    --submit \\
    --screenshot /tmp/results.png

Field matching:
  Fields are matched by: name attribute, label text, placeholder, or aria-label.
  For complex forms, use CSS selectors: --selector "input#email" --value "test@example.com"

Environment variables:
  HEADLESS=1    Run browser in headless mode
  SLOW_MO=250   Slow down actions by 250ms
""",
    )
    parser.add_argument("url", help="URL of the form")
    parser.add_argument(
        "-f",
        "--field",
        action="append",
        default=[],
        help="Field to fill (format: name=value). Can be repeated.",
    )
    parser.add_argument(
        "--selector",
        action="append",
        default=[],
        help="CSS selector for field (use with --value)",
    )
    parser.add_argument(
        "--value",
        action="append",
        default=[],
        help="Value for selector (pairs with --selector)",
    )
    parser.add_argument("--submit", action="store_true", help="Submit the form after filling")
    parser.add_argument("--screenshot", help="Take screenshot after filling")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    if len(args.selector) != len(args.value):
        print("Error: --selector and --value must be paired", file=sys.stderr)
        return 1

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

            # Fill by name/label/placeholder
            for field in args.field:
                try:
                    name, value = parse_field(field)

                    # Try different locator strategies
                    filled = False

                    # Try by label
                    label_locator = page.get_by_label(name)
                    if label_locator.count() > 0:
                        label_locator.first.fill(value)
                        print(f"  Filled by label: {name}")
                        filled = True

                    # Try by placeholder
                    if not filled:
                        placeholder_locator = page.get_by_placeholder(name)
                        if placeholder_locator.count() > 0:
                            placeholder_locator.first.fill(value)
                            print(f"  Filled by placeholder: {name}")
                            filled = True

                    # Try by name attribute
                    if not filled:
                        name_locator = page.locator(f"[name='{name}']")
                        if name_locator.count() > 0:
                            name_locator.first.fill(value)
                            print(f"  Filled by name: {name}")
                            filled = True

                    # Try by id
                    if not filled:
                        id_locator = page.locator(f"#{name}")
                        if id_locator.count() > 0:
                            id_locator.first.fill(value)
                            print(f"  Filled by id: {name}")
                            filled = True

                    if not filled:
                        print(f"  Warning: Could not find field: {name}", file=sys.stderr)

                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    return 1

            # Fill by CSS selector
            for selector, value in zip(args.selector, args.value):
                page.locator(selector).fill(value)
                print(f"  Filled selector: {selector}")

            # Submit if requested
            if args.submit:
                # Try to find and click submit button
                submit_btn = page.get_by_role("button", name="submit")
                if submit_btn.count() == 0:
                    submit_btn = page.locator("button[type='submit'], input[type='submit']")

                if submit_btn.count() > 0:
                    submit_btn.first.click()
                    page.wait_for_load_state("networkidle")
                    print("  Form submitted")
                else:
                    # Try pressing Enter on last filled field
                    page.keyboard.press("Enter")
                    page.wait_for_load_state("networkidle")
                    print("  Pressed Enter to submit")

            # Screenshot if requested
            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=True)
                print(f"Screenshot: {args.screenshot}")

            print(f"\nFinal URL: {page.url}")
            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            error_path = f"/tmp/form-error-{ts}.png"
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
