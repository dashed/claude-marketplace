#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.56.0"]
# ///
"""Check Playwright browser installation status."""

import sys

from playwright.sync_api import sync_playwright


def main() -> int:
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
                print(f"  {name}: {path}")
            except Exception:
                missing.append(name)
                print(f"  {name}: missing")

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
