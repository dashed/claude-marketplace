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

## Reference Script (Git + jj — Dual VCS)

Full-featured script showing both jj and git status independently (both appear for colocated repos):

```bash
#!/bin/bash
input=$(cat)

model_name=$(echo "$input" | jq -r '.model.display_name')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')

# Build VCS info — jj and git are checked independently (both can show for colocated repos)
vcs_info=""

# jj repository check
if jj root -R "$current_dir" --ignore-working-copy >/dev/null 2>&1; then
    # NB: every field needs a non-empty placeholder — IFS=tab read collapses
    # consecutive tabs (tab is IFS whitespace), so an empty field would shift
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
                if [ "$ahead" -gt 0 ]; then
                    status_parts+=("${ahead} ahead")
                fi
                if [ "$behind" -gt 0 ]; then
                    status_parts+=("${behind} behind")
                fi
            fi
        fi

        if [ -n "$bookmarks" ]; then
            display="${bookmarks} @ ${change_id}"
        else
            display="@ ${change_id}"
        fi

        if [ ${#status_parts[@]} -eq 0 ]; then
            vcs_info=" [jj ${display}]"
        else
            status=$(printf '%s, ' "${status_parts[@]}"); status=${status%, }
            vcs_info=" [jj ${display}: ${status}]"
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
        if [ "$staged_count" -gt 0 ]; then
            status_parts+=("${staged_count} staged")
        fi

        modified_count=$(git -C "$current_dir" diff --numstat 2>/dev/null | wc -l | tr -d ' ')
        if [ "$modified_count" -gt 0 ]; then
            status_parts+=("${modified_count} modified")
        fi

        untracked_count=$(git -C "$current_dir" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
        if [ "$untracked_count" -gt 0 ]; then
            status_parts+=("${untracked_count} untracked")
        fi

        upstream=$(git -C "$current_dir" rev-parse --abbrev-ref @{upstream} 2>/dev/null)
        if [ -n "$upstream" ]; then
            ahead=$(git -C "$current_dir" rev-list --count @{upstream}..HEAD 2>/dev/null)
            behind=$(git -C "$current_dir" rev-list --count HEAD..@{upstream} 2>/dev/null)
            if [ "$ahead" -gt 0 ]; then
                status_parts+=("${ahead} ahead")
            fi
            if [ "$behind" -gt 0 ]; then
                status_parts+=("${behind} behind")
            fi
        fi

        if [ ${#status_parts[@]} -eq 0 ]; then
            vcs_info="${vcs_info} [git ${branch}]"
        else
            status=$(printf '%s, ' "${status_parts[@]}"); status=${status%, }
            vcs_info="${vcs_info} [git ${branch}: ${status}]"
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
            vcs_info="${vcs_info} [jj ⇄ git out of sync: ${sync}]"
        else
            vcs_info="${vcs_info} [jj ⇄ git out of sync]"
        fi
    fi
fi

echo "${model_name} | ${current_dir}${vcs_info}"
```

## Output Examples

```
# Colocated jj+git repo (both shown)
Opus 4.6 | /path/to/project [jj feature @ znnuytsz: 1 modified, 2 ahead] [git feature: 1 untracked]
# jj-only (non-colocated)
Opus 4.6 | /path/to/project [jj @ uoylmlmx]
# jj with conflict and remote tracking
Opus 4.6 | /path/to/project [jj main @ kntqzsqt: conflict, 3 modified, 1 behind]
# git-only repo
Opus 4.6 | /path/to/project [git master: 2 staged, 1 modified]
# Detached HEAD (checkout by hash, bisect, jj-colocated)
Opus 4.6 | /path/to/project [git detached @ d7ead68: 1 modified]
# Colocated repo where git moved without jj noticing (e.g. direct git commit)
Opus 4.6 | /path/to/project [jj @ snzksmsp] [git detached @ 76137d1] [jj ⇄ git out of sync: git +1]
# No VCS
Opus 4.6 | /tmp
```

## Design Notes

- **Dual VCS**: Both jj and git blocks run independently; colocated repos show both
- **jj ahead/behind**: Uses `commit_id` (renders as full git commit hash) then `git rev-list --count` against the first bookmark's remote tracking ref
- **Detached HEAD fallback**: `git branch --show-current` prints nothing when detached, so the git segment falls back to `detached @ <short-hash>`. Without this, jj-colocated repos would *never* show the git segment — jj keeps git permanently detached
- **jj ⇄ git sync check**: compares `git rev-parse HEAD` with jj's last-imported `git_head()`; the segment appears only when they diverge, with directional counts (`git +N` / `jj +N`). Divergence happens when git commands run without a jj command following — and stays visible because this script's `--ignore-working-copy` calls never trigger jj's auto-import
- **IFS tab gotcha**: every jj template field needs a non-empty placeholder (`"-"`) — tab is IFS *whitespace*, so `read` collapses consecutive tabs instead of preserving empty fields. An empty field shifts the columns (this bug once made every repo show `conflict` and silently disabled jj ahead/behind)
- **`--ignore-working-copy`**: Prevents expensive snapshot operations in the statusline
- **`--no-pager`**: Ensures jj doesn't page when running non-interactively
- **Performance**: 2-3 subprocess calls for jj, 3-5 for git, plus 2-3 for the sync check in colocated repos; acceptable for statusline frequency

## Multi-Line Example

Add context usage as a second line:

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

## Prerequisites

- `jq` (for parsing JSON input)
- `git` (for git repo detection)
- `jj` >= 0.36 (optional, for jj repo support)
