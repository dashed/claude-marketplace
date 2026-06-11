# fzf Feature → Minimum Version

A consolidated lookup of **which fzf version introduced a feature** this skill documents, so you know what works on an older (or newer) fzf. Use it to answer "is my fzf new enough for X?" and "what do I need to upgrade to?"

**How to read this:**
- Versions are when a feature was **introduced** (sometimes experimental or unstable first; defaults/rebinds may come later — those are noted).
- fzf has no 1.0 release yet; all versions are `0.x.y`. A `MINOR` bump (`0.x`) is fzf's feature release; bug-fix-only point releases (`0.73.1`) rarely add surface and are noted inline when relevant.
- Features **not listed here are long-standing** (predate ~0.38 / early 2023 — e.g. core extended-search syntax, `CTRL-T`/`CTRL-R`/`ALT-C`, basic `--preview`/`--height`/`--layout`/`--border`, `--bind`, `reload`/`execute`/`preview` actions, `--nth`/`--with-nth`/`--delimiter`, field placeholders). This file deliberately omits them to stay signal-rich.
- This skill is documented against **fzf 0.73.x**. Always confirm on the running system: `fzf --version`, then `man fzf` (or `fzf --man`).

Every version below was verified by locating the feature **under its introducing section header** in the fzf source `CHANGELOG.md` (cross-checked against `man/man1/fzf.1`). Versions were **not** inferred from usage examples — later release notes frequently cite older flags in examples, so each entry was traced to its own "Added …" line.

## Contents

- [fzf 0.70 and newer](#fzf-070-and-newer)
- [fzf 0.60 to 0.69](#fzf-060-to-069)
- [fzf 0.50 to 0.59](#fzf-050-to-059)
- [fzf 0.38 to 0.49](#fzf-038-to-049)
- [Removed, deprecated, and changed defaults](#removed-deprecated-and-changed-defaults)

## fzf 0.70 and newer

| Min version | Feature | Area |
|---|---|---|
| 0.73 | Nushell shell integration — `fzf --nushell` (and installer support) | shell integration |
| 0.73 | `--preview-window=next` (preview adjacent to the input section, on the list side) | preview |
| 0.73 | `every(N)` timer-driven event for `--bind` (`N` in seconds) | events |
| 0.73 | `$FZF_IDLE_TIME` / `$FZF_IDLE_TIME_MS` env vars (time since last user activity) | events / env |
| 0.73 | `$FZF_CURRENT_ITEM` env var (current item, for shells where quoting `{}` is awkward) | env |
| 0.72 | `inline` style for `--header-border` / `--header-lines-border` / `--footer-border` (section embedded in the list frame) | borders |
| 0.72 | `dashed` border style (`--border=dashed`, `--list-border=dashed`, …) | borders |
| 0.71 | `--popup` (tmux popup **or** Zellij floating pane); requires tmux 3.3+ or Zellij 0.44+ | tmux / Zellij |
| 0.71 | `--id-nth=NTH` — cross-reload item identity (used with `--track` to keep the cursor on the same item across `reload`) | tracking / reload |
| 0.70 | `change-with-nth` action (dynamically change `--with-nth`; requires `--with-nth` set initially) | fields |
| 0.70 | `change-header-lines` action (dynamically change `--header-lines`) | header |

## fzf 0.60 to 0.69

| Min version | Feature | Area |
|---|---|---|
| 0.68 | `--wrap=word` (alias `--wrap-word`) + `toggle-wrap-word` action — word-level wrapping in the list | list wrapping |
| 0.68 | `--preview-window wrap-word` flag + `toggle-preview-wrap-word` action | preview wrapping |
| 0.68 | `--preview-wrap-sign` (custom wrap indicator for the preview window) | preview |
| 0.68 | `alt-gutter` color; `--color` underline variants (`underline-double`/`-curly`/`-dotted`/`-dashed`) | color |
| 0.68 | `$FZF_WRAP` env var (`char` or `word` when wrapping is enabled) | env |
| 0.67 | `--freeze-left=N` / `--freeze-right=N` (keep leftmost/rightmost N columns always visible) | columns |
| 0.66 | "raw" mode — `--raw`, `toggle-raw` / `enable-raw` / `disable-raw`, `up-match` / `down-match` / `best` actions, `$FZF_RAW` env var, `nomatch` color | raw mode |
| 0.66 | `--gutter CHAR` and `--gutter-raw CHAR` (customize the gutter column character) | gutter |
| 0.66 | `--listen` Unix-domain-socket support (path ending in `.sock`) | server / `--listen` |
| 0.63 | Footer — `--footer[=STRING]`, `--footer-border`, `--footer-label`, `--footer-label-pos`; `change-footer` / `transform-footer` / `bg-transform-footer` (+ `*-footer-label`) actions; `footer*` colors | footer |
| 0.63 | `bg-transform*` async actions + `bg-cancel`; `{*}` placeholder (all matched items) | async actions / placeholders |
| 0.61 | `change-ghost` / `transform-ghost` (ghost text); `change-pointer` / `transform-pointer` (pointer sign) | actions |
| 0.60 | `--accept-nth=N[,..]` (choose output fields on accept; also works in `--filter` batch mode; template form `'{1}:{2}'`) | fields / output |

## fzf 0.50 to 0.59

| Min version | Feature | Area |
|---|---|---|
| 0.59 | `--header-lines-border` (separate border for `--header-lines` rows) | header / borders |
| 0.59 | `transform-nth` action; `search` / `transform-search` actions; `$FZF_CLICK_HEADER_WORD` / `$FZF_CLICK_HEADER_NTH` on `click-header` | search / header |
| 0.59 | `--scheme=path` sets `--tiebreak=pathname,length`; new `pathname` tiebreak (prioritize file-name matches) | scoring |
| 0.58 | `--list-border`, `--input-border`, `--header-border` border types; `--style` presets (e.g. `--style full`) | borders / style |
| 0.55 | `'wild'` exact-boundary-match (term single-quoted at both ends → exact match with both ends at word boundaries) | search syntax |
| 0.54 | `--wrap` (char-level line wrap) + `--wrap-sign` + `toggle-wrap` action | list wrapping |
| 0.53 | `--tmux` option (built-in tmux popup; replaces the `fzf-tmux` script — needs tmux 3.3+) | tmux |

## fzf 0.38 to 0.49

| Min version | Feature | Area |
|---|---|---|
| 0.48 | Shell-integration flags `--bash` / `--zsh` / `--fish` (scripts embedded in the binary) | shell integration |
| 0.45 | `transform` action (conditionally perform a series of actions from a command's output) | actions |
| 0.38 | `become(...)` action (replace fzf with a command via `execve(2)`; **not** on Windows until 0.51) | actions |

## Removed, deprecated, and changed defaults

These matter most when a script or habit assumes old behavior — or when you read older docs.

| Version | Change |
|---|---|
| 0.71 | **Default change:** `--tmux` is now an **alias for `--popup`** (which also targets Zellij). Behavior is unchanged for plain tmux users. |
| 0.71 | **Requirement:** fish shell integration now requires **fish 3.4.0+**. |
| 0.68 | **Default change:** `ctrl-/` and `alt-/` rebound from `toggle-wrap` to **`toggle-wrap-word`** (word-level wrapping). |
| 0.66 | **Default change:** `CTRL-N` / `CTRL-P` now run **`down-match` / `up-match`** (still `next-history` / `prev-history` when `--history` is set — rebind or use `ALT-DOWN` / `ALT-UP`). Gutter narrowed (`▌`); markers no longer use background colors. |
| 0.54 | **Default binding (introduced):** `ctrl-/` and `alt-/` bound to `toggle-wrap` (later changed to `toggle-wrap-word` in 0.68). |
| 0.51 | **Platform:** `become` action gains **Windows** support (unsupported when introduced in 0.38). |

> Note on tmux/Zellij popups: `--tmux` / `--popup` require **tmux 3.3+**; Zellij floating-pane support (via `--popup`, or `--tmux` as its alias) requires **Zellij 0.44+** and arrived in **0.71**. The legacy external `fzf-tmux` script still exists but `--tmux` (0.53) is the recommended replacement.
