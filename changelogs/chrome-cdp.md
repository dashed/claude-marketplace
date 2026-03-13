# Changelog - chrome-cdp

All notable changes to the chrome-cdp skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-03-13

### Added
- Initial addition to marketplace
- Lightweight Chrome DevTools Protocol CLI for interacting with live Chrome sessions
- 13 commands: list, snap, eval, shot, html, nav, net, click, clickxy, type, loadall, evalraw, stop
- Per-tab persistent daemon architecture (Chrome "Allow debugging" modal fires only once)
- Python implementation using `python -m chrome_cdp` (adapted from original Node.js version by Petr Baudis)
- references/coordinate-system.md: DPR detection, CSS pixel mapping, worked examples
- references/daemon-ipc.md: Unix socket NDJSON protocol, request/response schema, command list
- Based on [chrome-cdp-skill](https://github.com/pasky/chrome-cdp-skill) by Petr Baudis
