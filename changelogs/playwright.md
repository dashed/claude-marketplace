# Changelog - playwright

All notable changes to the playwright skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2025-12-06

### Added
- Initial addition to marketplace
- Browser automation with Playwright for Python using uv inline scripts
- Scripts for common operations:
  - `check_setup.py` - Verify browser installation
  - `screenshot.py` - Take screenshots with viewport and full-page options
  - `navigate.py` - Navigate and extract page content (title, links, text, HTML)
  - `fill_form.py` - Fill and submit forms with multiple locator strategies
  - `evaluate.py` - Execute JavaScript in browser context
- Comprehensive reference documentation:
  - `api-reference.md` - Full Playwright Python API quick reference
  - `selectors.md` - Selector patterns and best practices
  - `custom-scripts.md` - Guide for writing custom automation scripts
  - `troubleshooting.md` - Common issues and solutions
- Modern locator API patterns (get_by_role, get_by_label, etc.)
- Environment variable configuration (HEADLESS, SLOW_MO, VIEWPORT, TRACE)
- PEP 723 inline script metadata for self-contained scripts
- Pinned to Playwright 1.56.0 for version stability
