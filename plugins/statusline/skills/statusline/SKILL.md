---
name: statusline
description: Configure the Claude Code status line with VCS-aware scripts showing git branch, jj change ID, bookmarks, context usage, and costs. Use when setting up a statusline, customizing the status bar, adding git or jj info to the prompt, configuring statusLine in settings.json, or troubleshooting statusline scripts.
---

# Statusline Configuration

## Overview

Claude Code supports a custom status line via a shell script that receives JSON session data on stdin and outputs text to stdout. The script runs after each assistant message, after `/compact`, on permission mode changes, and on vim mode toggles (debounced at 300ms). Supports multiple lines, ANSI colors, and OSC 8 hyperlinks.

## Setup

Configure in `~/.claude/settings.json` (or project settings):

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

Optional fields:
- `padding` (int): extra horizontal spacing in characters (default: 0)
- `refreshInterval` (int): re-run every N seconds in addition to event-driven updates (min: 1)
- `hideVimModeIndicator` (bool): suppress built-in `-- INSERT --` when script renders vim mode

Alternatively, use an inline command:

```json
{
  "statusLine": {
    "type": "command",
    "command": "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0)% context\"'"
  }
}
```

Or use `/statusline <description>` to have Claude generate one automatically.

## Available JSON Fields

The script receives JSON on stdin with these fields:

| Field | Description |
|-------|-------------|
| `model.id`, `model.display_name` | Model identifier and display name |
| `cwd`, `workspace.current_dir` | Current working directory |
| `workspace.project_dir` | Directory where Claude Code was launched |
| `workspace.added_dirs` | Additional directories added via `/add-dir` |
| `workspace.git_worktree` | Git worktree name (if in linked worktree) |
| `workspace.repo.host/owner/name` | Repository identity from `origin` remote |
| `cost.total_cost_usd` | Estimated session cost in USD |
| `cost.total_duration_ms` | Wall-clock time since session start |
| `cost.total_api_duration_ms` | Time spent waiting for API responses |
| `cost.total_lines_added/removed` | Lines of code changed |
| `context_window.used_percentage` | Percentage of context window used |
| `context_window.remaining_percentage` | Percentage remaining |
| `context_window.context_window_size` | Max context window (200000 or 1000000) |
| `context_window.total_input_tokens` | Input tokens in current context |
| `context_window.total_output_tokens` | Output tokens from last response |
| `exceeds_200k_tokens` | Whether tokens exceed 200k threshold |
| `effort.level` | Reasoning effort (low/medium/high/xhigh/max) |
| `thinking.enabled` | Whether extended thinking is enabled |
| `rate_limits.five_hour.used_percentage` | 5-hour rate limit usage (Pro/Max only) |
| `rate_limits.seven_day.used_percentage` | 7-day rate limit usage (Pro/Max only) |
| `session_id` | Unique session identifier |
| `session_name` | Custom name from `--name` or `/rename` |
| `version` | Claude Code version |
| `vim.mode` | Current vim mode (NORMAL/INSERT/VISUAL) |
| `agent.name` | Agent name if using `--agent` |
| `pr.number`, `pr.url`, `pr.review_state` | Open PR info for current branch |
| `worktree.name/path/branch` | Worktree info during `--worktree` sessions |

Fields marked may be absent or null - use `jq` fallbacks like `// 0` or `// empty`.

**No terminal width in the JSON.** There is no `columns`/`width`/`lines` field here. To lay out responsively (and wrap long lines), read the `COLUMNS`/`LINES` environment variables instead — see [Responsive Width-Aware Wrapping](#responsive-width-aware-wrapping).

## Reference Script (Git + jj — Dual VCS)

Full-featured, width-aware script showing both jj and git status independently (both appear for colocated repos), plus context-window usage. It ends with a greedy segment packer (see [Responsive Width-Aware Wrapping](#responsive-width-aware-wrapping)) so a long line wraps cleanly at segment boundaries on narrow terminals while rendering identically on wide ones:

```bash
#!/bin/bash

input=$(cat)

model_name=$(echo "$input" | jq -r '.model.display_name')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

# Build VCS info — jj and git are checked independently (both show for colocated repos).
# Each discrete block is pushed as one breakable segment so the width-aware packer
# at the bottom can wrap cleanly at block boundaries on narrow terminals.
vcs_segments=()

# jj repository check
if jj root -R "$current_dir" --ignore-working-copy >/dev/null 2>&1; then
    # NB: every field needs a non-empty placeholder — IFS=tab read collapses
    # consecutive tabs (tab is IFS whitespace), so empty fields would shift
    # the columns.
    jj_data=$(jj --no-pager --ignore-working-copy -R "$current_dir" log --no-graph -r @ -T 'if(local_bookmarks, local_bookmarks.join(","), "-") ++ "\t" ++ change_id.short(8) ++ "\t" ++ if(conflict, "conflict", "-") ++ "\t" ++ commit_id' 2>/dev/null)

    if [ -n "$jj_data" ]; then
        IFS=$'\t' read -r bookmarks change_id conflict_status commit_hash <<< "$jj_data"
        if [ "$bookmarks" = "-" ]; then bookmarks=""; fi
        if [ "$conflict_status" = "-" ]; then conflict_status=""; fi

        modified_count=$(jj --no-pager --ignore-working-copy -R "$current_dir" diff --summary 2>/dev/null | wc -l | tr -d ' ')

        status_parts=()
        if [ -n "$conflict_status" ]; then
            status_parts+=("conflict")
        fi
        if [ "$modified_count" -gt 0 ]; then
            status_parts+=("${modified_count} modified")
        fi

        # Ahead/behind remote tracking (works in colocated repos via git)
        if [ -n "$bookmarks" ] && [ -n "$commit_hash" ]; then
            first_bookmark=$(echo "$bookmarks" | cut -d',' -f1)
            if git -C "$current_dir" rev-parse --verify "origin/$first_bookmark" >/dev/null 2>&1; then
                remote_ref=$(git -C "$current_dir" rev-parse "origin/$first_bookmark" 2>/dev/null)
                ahead=$(git -C "$current_dir" rev-list --count "$remote_ref..$commit_hash" 2>/dev/null)
                behind=$(git -C "$current_dir" rev-list --count "$commit_hash..$remote_ref" 2>/dev/null)
                if [ "$ahead" -gt 0 ]; then status_parts+=("${ahead} ahead"); fi
                if [ "$behind" -gt 0 ]; then status_parts+=("${behind} behind"); fi
            fi
        fi

        if [ -n "$bookmarks" ]; then
            display="${bookmarks} @ ${change_id}"
        else
            display="@ ${change_id}"
        fi

        if [ ${#status_parts[@]} -eq 0 ]; then
            vcs_segments+=("[jj ${display}]")
        else
            status=$(printf '%s, ' "${status_parts[@]}"); status=${status%, }
            vcs_segments+=("[jj ${display}: ${status}]")
        fi
    fi
fi

# git repository check (independent — shows alongside jj for colocated repos)
if git -C "$current_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git -C "$current_dir" branch --show-current 2>/dev/null)
    if [ -z "$branch" ]; then
        # Detached HEAD (git checkout <hash>, bisect, jj-colocated repos):
        # --show-current prints nothing, so fall back to the short hash.
        detached=$(git -C "$current_dir" rev-parse --short HEAD 2>/dev/null)
        [ -n "$detached" ] && branch="detached @ ${detached}"
    fi
    if [ -n "$branch" ]; then
        status_parts=()

        staged_count=$(git -C "$current_dir" diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
        if [ "$staged_count" -gt 0 ]; then status_parts+=("${staged_count} staged"); fi

        modified_count=$(git -C "$current_dir" diff --numstat 2>/dev/null | wc -l | tr -d ' ')
        if [ "$modified_count" -gt 0 ]; then status_parts+=("${modified_count} modified"); fi

        untracked_count=$(git -C "$current_dir" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
        if [ "$untracked_count" -gt 0 ]; then status_parts+=("${untracked_count} untracked"); fi

        upstream=$(git -C "$current_dir" rev-parse --abbrev-ref @{upstream} 2>/dev/null)
        if [ -n "$upstream" ]; then
            ahead=$(git -C "$current_dir" rev-list --count @{upstream}..HEAD 2>/dev/null)
            behind=$(git -C "$current_dir" rev-list --count HEAD..@{upstream} 2>/dev/null)
            if [ "$ahead" -gt 0 ]; then status_parts+=("${ahead} ahead"); fi
            if [ "$behind" -gt 0 ]; then status_parts+=("${behind} behind"); fi
        fi

        if [ ${#status_parts[@]} -eq 0 ]; then
            vcs_segments+=("[git ${branch}]")
        else
            status=$(printf '%s, ' "${status_parts[@]}"); status=${status%, }
            vcs_segments+=("[git ${branch}: ${status}]")
        fi
    fi
fi

# jj ⇄ git sync check (colocated repos): compare git's actual HEAD with jj's
# last-imported view of it (git_head()). They diverge when git moves without a
# jj command running afterward — and the jj calls above use
# --ignore-working-copy precisely so this script never triggers the re-import.
if [ -n "$jj_data" ]; then
    jj_git_head=$(jj --no-pager --ignore-working-copy -R "$current_dir" log --no-graph -r 'git_head()' -T 'commit_id' 2>/dev/null)
    git_head=$(git -C "$current_dir" rev-parse HEAD 2>/dev/null)
    if [ -n "$jj_git_head" ] && [ -n "$git_head" ] && [ "$jj_git_head" != "$git_head" ]; then
        git_ahead=$(git -C "$current_dir" rev-list --count "$jj_git_head..$git_head" 2>/dev/null || echo 0)
        jj_ahead=$(git -C "$current_dir" rev-list --count "$git_head..$jj_git_head" 2>/dev/null || echo 0)
        sync_parts=()
        [ "${git_ahead:-0}" -gt 0 ] && sync_parts+=("git +${git_ahead}")
        [ "${jj_ahead:-0}" -gt 0 ] && sync_parts+=("jj +${jj_ahead}")
        if [ ${#sync_parts[@]} -gt 0 ]; then
            sync=$(printf '%s, ' "${sync_parts[@]}"); sync=${sync%, }
            vcs_segments+=("[jj ⇄ git out of sync: ${sync}]")
        else
            vcs_segments+=("[jj ⇄ git out of sync]")
        fi
    fi
fi

# --- Width-aware greedy segment packer ---------------------------------------
# Each entry in segs[] is one breakable unit; seps[i] is the separator placed
# before segs[i] when it shares a line with the previous segment. A segment
# that wraps to a new line starts that line with no leading separator. On a
# wide terminal everything packs onto one line and reproduces the original
# "model | dir [jj ...] [git ...] | ctx N%" layout byte-for-byte; on a narrow
# terminal it breaks at segment boundaries instead of overflowing.
#
# Width source: Claude Code (v2.1.153+) exports COLUMNS before running this
# script; stdout is captured (not a TTY), so tput/stty cannot detect width.
cols=${COLUMNS:-80}            # 80 = fallback for older Claude Code / non-CC shells
budget=$((cols - 2))           # small margin; built-in padding width is undocumented
[ "$budget" -lt 10 ] && budget=10

segs=("$model_name" "$current_dir")
seps=("" " | ")
for seg in "${vcs_segments[@]}"; do
    segs+=("$seg"); seps+=(" ")
done
segs+=("ctx ${pct}%"); seps+=(" | ")

# NB: no ANSI/OSC 8 escapes are emitted here, so ${#seg} == display width.
# If color/hyperlinks are added later, measure an escape-stripped shadow copy
# (sed -E 's/\x1b\[[0-9;]*m//g') so segments don't wrap early.
line=""; linelen=0; out=()
for i in "${!segs[@]}"; do
    seg="${segs[$i]}"
    [ -z "$seg" ] && continue
    # A single segment wider than the line (usually a long current_dir) can't
    # break at a boundary — truncate it, keeping the tail, with a leading "…".
    if [ "${#seg}" -gt "$budget" ]; then
        seg="…${seg: -$((budget - 1))}"
    fi
    slen=${#seg}
    sep="${seps[$i]}"; seplen=${#sep}
    if [ -z "$line" ]; then
        line="$seg"; linelen=$slen
    elif [ $((linelen + seplen + slen)) -le "$budget" ]; then
        line+="${sep}${seg}"; linelen=$((linelen + seplen + slen))
    else
        out+=("$line"); line="$seg"; linelen=$slen   # wrap to next line
    fi
done
[ -n "$line" ] && out+=("$line")
printf '%s\n' "${out[@]}"
```

## Output Examples

On a terminal wide enough to fit the line, everything packs onto one row (identical to a non-wrapping script):

```
# Colocated jj+git repo (both shown)
Opus 4.6 | /path/to/project [jj feature @ znnuytsz: 1 modified, 2 ahead] [git feature: 1 untracked] | ctx 12%
# jj-only (non-colocated)
Opus 4.6 | /path/to/project [jj @ uoylmlmx] | ctx 12%
# jj with conflict and remote tracking
Opus 4.6 | /path/to/project [jj main @ kntqzsqt: conflict, 3 modified, 1 behind] | ctx 12%
# git-only repo
Opus 4.6 | /path/to/project [git master: 2 staged, 1 modified] | ctx 12%
# Detached HEAD (checkout by hash, bisect, jj-colocated)
Opus 4.6 | /path/to/project [git detached @ d7ead68: 1 modified] | ctx 12%
# Colocated repo where git moved without jj noticing (e.g. direct git commit)
Opus 4.6 | /path/to/project [jj @ snzksmsp] [git detached @ 76137d1] [jj ⇄ git out of sync: git +1] | ctx 12%
# No VCS
Opus 4.6 | /tmp | ctx 12%
```

On a narrow terminal the same line wraps at segment boundaries instead of overflowing (the git-only repo above at `COLUMNS=40`):

```
Opus 4.6 | /path/to/project
[git master: 2 staged, 1 modified]
ctx 12%
```

## Design Notes

- **Dual VCS**: Both jj and git blocks run independently; colocated repos show both
- **jj ahead/behind**: Uses `commit_id` (renders as full git commit hash) then `git rev-list --count` against the first bookmark's remote tracking ref
- **Detached HEAD fallback**: `git branch --show-current` prints nothing when detached, so the git segment falls back to `detached @ <short-hash>`. Without this, jj-colocated repos would *never* show the git segment — jj keeps git permanently detached
- **jj ⇄ git sync check**: compares `git rev-parse HEAD` with jj's last-imported `git_head()`; the segment appears only when they diverge, with directional counts (`git +N` / `jj +N`). Divergence happens when git commands run without a jj command following — and stays visible because this script's `--ignore-working-copy` calls never trigger jj's auto-import
- **IFS tab gotcha**: every jj template field needs a non-empty placeholder (`"-"`) — tab is IFS *whitespace*, so `read` collapses consecutive tabs instead of preserving empty fields. An empty field shifts the columns (this bug once made every repo show `conflict` and silently disabled jj ahead/behind)
- **`--ignore-working-copy`**: Prevents expensive snapshot operations in the statusline
- **`--no-pager`**: Ensures jj doesn't page when running non-interactively
- **Width-aware wrapping**: the final block packs segments (model, dir, each VCS block, `ctx`) onto lines using a *parallel* `seps[]` array, so a wide terminal renders the original single line unchanged (model→dir and →`ctx` join with `" | "`; VCS blocks hug the dir with a space) while a narrow one wraps at segment boundaries. Width comes from `COLUMNS` (`${COLUMNS:-80}`); an over-wide `current_dir` is tail-truncated with a leading `…`. See [Responsive Width-Aware Wrapping](#responsive-width-aware-wrapping)
- **Performance**: 2-3 subprocess calls for jj, 3-5 for git, plus 2-3 for the sync check in colocated repos; acceptable for statusline frequency

## Multi-Line Example

For a deliberately multi-line layout (independent of the width packer), add a context bar as a second line:

```bash
#!/bin/bash
input=$(cat)
model_name=$(echo "$input" | jq -r '.model.display_name')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
cost=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')

# Line 1: model + dir + VCS (add VCS logic from above)
echo "${model_name} | ${current_dir}"

# Line 2: context bar + cost
bar_width=20
filled=$((pct * bar_width / 100))
printf -v bar '%*s' "$filled" ''
printf -v empty '%*s' "$((bar_width - filled))" ''
echo "[${bar// /▓}${empty// /░}] ${pct}%  \$${cost}"
```

## Responsive Width-Aware Wrapping

The reference script above ends with a greedy segment packer so a long statusline wraps cleanly instead of overflowing — Claude Code's docs warn that overflow "may get truncated or wrap awkwardly." This section explains how that packer works so you can adapt it.

**Width source — `COLUMNS`/`LINES` env vars only.** Claude Code sets `COLUMNS` and `LINES` to the current terminal dimensions before running the script (**requires Claude Code v2.1.153+**). Fall back to a default for older versions:

```bash
cols=${COLUMNS:-80}
```

**What does NOT work, and why:** Claude Code captures the script's stdout (it is not connected to the TTY) and pipes the JSON in on stdin, so there is no terminal for the script to query. `tput cols`, `stty size`, language-level width detection, and `/dev/tty` are all non-functional/undocumented — `COLUMNS` is the only supported mechanism.

**Greedy segment packer.** The status is built as discrete logical segments — model, dir, each `[jj …]`/`[git …]`/`[jj ⇄ git …]` block, and `ctx` — in a `segs[]` array, with a *parallel* `seps[]` array giving the separator that precedes each segment when it shares a line. Per-segment separators (rather than one uniform separator) are what let a wide terminal reproduce the original `model | dir [jj …] [git …] | ctx N%` layout byte-for-byte: model→dir and →`ctx` join with `" | "`, while VCS blocks hug the dir with a bare space. The packer walks the segments, appending to the current line while the next segment fits the width budget and breaking to a new line otherwise:

```bash
cols=${COLUMNS:-80}          # set by Claude Code v2.1.153+; 80 = fallback
budget=$((cols - 2)); [ "$budget" -lt 10 ] && budget=10

# segs[] / seps[] built as in the reference script (model, dir, VCS blocks, ctx)
line=""; linelen=0; out=()
for i in "${!segs[@]}"; do
    seg="${segs[$i]}"; [ -z "$seg" ] && continue
    sep="${seps[$i]}"; slen=${#seg}; seplen=${#sep}
    if [ -z "$line" ]; then
        line="$seg"; linelen=$slen
    elif [ $((linelen + seplen + slen)) -le "$budget" ]; then
        line+="${sep}${seg}"; linelen=$((linelen + seplen + slen))
    else
        out+=("$line"); line="$seg"; linelen=$slen   # wrap to next line
    fi
done
[ -n "$line" ] && out+=("$line")
printf '%s\n' "${out[@]}"      # each line = a separate status row
```

Wide terminal → one line (identical to the non-wrapping output); narrow → wraps cleanly at segment boundaries.

**Caveats:**
- **ANSI/OSC 8 escapes inflate `${#seg}`** — it counts the escape bytes, so colored/hyperlinked segments wrap too early. The reference script emits no escapes, so `${#seg}` equals the display width; if you add color, measure a plain-text shadow copy of each segment (strip escapes with `sed -E 's/\x1b\[[0-9;]*m//g'`) and pack on that length while emitting the colored version.
- **A single segment wider than `budget`** (usually a long `current_dir`) can't break at a boundary. The reference script truncates such a segment to a leading `…` plus the tail (`seg="…${seg: -$((budget - 1))}"`) rather than letting it overflow.
- **`${#var}` counts code points, not display columns** — fine for ASCII, the `▓░` bar glyphs, and the `⇄` sync arrow (1 column each), but wide CJK/emoji may miscount. Acceptable as a statusline heuristic.

## Prerequisites

- `jq` (for parsing JSON input)
- `git` (for git repo detection)
- `jj` >= 0.36 (optional, for jj repo support)
```

