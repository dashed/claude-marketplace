# Conflict Resolution Reference

## How jj Stores Conflicts

jj records conflicts as first-class data inside commits, not as text markers in files. The stored representation is logical (a tree of merge inputs), not textual conflict markers. This means:

- Rebasing a conflicted commit never produces nested markers
- Conflicts survive rebase, merge, and other operations cleanly
- You can commit, share, and further rebase conflicted states

Conflict markers are only "materialized" into files when you check out a conflicted commit or view diffs.

## Conflict Marker Styles

Configure with: `ui.conflict-marker-style = "diff" | "snapshot" | "git"`

### diff style (default)

Shows a diff to apply against a snapshot. You mentally apply the diff to the snapshot to resolve.

```
<<<<<<< conflict 1 of 1
%%%%%%% diff from base to side A
 apple
-grape
+grapefruit
 orange
+++++++ side B snapshot
APPLE
GRAPE
ORANGE
>>>>>>> conflict 1 of 1 ends
```

Markers: `<<<<<<<` start, `%%%%%%%` diff section, `+++++++` snapshot section, `>>>>>>>` end. The `\\\\\\\` marker splits long labels across two lines.

**To resolve:** apply each diff to the snapshot content.

### snapshot style

Shows the full content of each side plus the base. Easier to read but requires manual comparison.

```
<<<<<<< conflict 1 of 1
+++++++ side A
apple
grapefruit
orange
------- base
apple
grape
orange
+++++++ side B
APPLE
GRAPE
ORANGE
>>>>>>> conflict 1 of 1 ends
```

### git style

Standard Git diff3 format. Useful for tool compatibility but only supports 2-sided conflicts.

```
<<<<<<< side A
apple
grapefruit
orange
||||||| base
apple
grape
orange
=======
APPLE
GRAPE
ORANGE
>>>>>>> side B
```

Falls back to snapshot style for conflicts with more than 2 sides.

## Resolution Workflows

### New commit + squash (safest)

```bash
jj new <conflicted>          # create child commit to work in
# edit files to resolve conflicts
jj squash                     # fold resolution into the conflicted commit
```

### Direct edit

```bash
jj edit <conflicted>          # check out the conflicted commit directly
# edit files to resolve conflicts
jj new                        # move on (resolution is already in the commit)
```

### External merge tool

```bash
jj resolve                    # launch configured merge tool on first conflicted file
jj resolve --list             # list all conflicted files
jj resolve <path>             # resolve a specific file
jj resolve --tool=meld        # use a specific tool
```

### Pick a side

```bash
jj resolve --tool :ours       # keep "our" side for a file
jj resolve --tool :theirs     # keep "their" side for a file
jj restore --from <rev> <path>  # restore a file from a specific revision
```

## Multi-Sided Conflicts

When merging 3+ commits at once, jj produces multi-sided conflicts. In diff style, you'll see one snapshot section (`+++++++`) and multiple diff sections (`%%%%%%%`). Resolve by applying each diff to the snapshot one at a time.

Multi-sided conflicts are where jj's diff-style markers shine — you don't need to manually compare all sides against each other.

## Binary File Conflicts

Binary files can't use text markers. Resolve by picking a version:

```bash
jj restore --from <rev> <path>    # take the file from a specific revision
```

## Partial Resolution

You can resolve some conflicted files while leaving others unresolved. jj tracks conflict state per-file, so partially resolved commits are valid. Use `jj resolve --list` to see remaining conflicts.

## Advantages of First-Class Conflicts

- **No `--continue` workflows** — resolve conflicts at any time by editing the commit, no special state to manage
- **Auto-rebase works through conflicts** — descendants rebase automatically even when ancestors are conflicted
- **Correct merge commit rebasing** — conflict resolutions in merge commits are preserved, unlike Git
- **Deferred resolution** — keep WIP commits rebased on trunk; resolve conflicts when you're ready
- **Collaborative resolution** — conflicted commits can be shared (when all collaborators use jj)
- **Trivial criss-cross and octopus merges** — cases that produce nested markers in Git are handled cleanly
