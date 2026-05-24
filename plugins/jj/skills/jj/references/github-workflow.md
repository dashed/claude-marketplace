# GitHub/GitLab Workflow

## Pushing Changes

### Using Auto-Generated Bookmarks

Let jj create a bookmark name from the change ID — no manual naming needed:

```shell
# Work on your changes, then commit
jj new main
jj commit -m 'feat(bar): add support for bar'

# Push parent of working copy (@ is empty), auto-creates push-XXXX bookmark
jj git push --change @-
# Short form: jj git push -c @-

# Push a specific change by its short ID
jj git push -c mw  # creates bookmark like "push-mwmpwkwknuz"
```

### Using Named Bookmarks

```shell
jj new main
jj commit -m 'feat(bar): add support for bar'

# Create bookmark on parent of working copy
jj bookmark create bar -r @-

# Track so push knows about it
jj bookmark track bar

# Push (only pushes tracked bookmarks with local changes)
jj git push
```

## Updating Your Repository

There is no `jj pull`. Use fetch + rebase:

```shell
# Fetch latest from remote
jj git fetch

# Rebase current branch onto updated main
jj rebase -d main

# Rebase multiple branches
jj rebase -b feature-a -b feature-b -d main
```

## Addressing PR Review Comments

### Additive Style (GitHub default)

GitHub compares branches, so adding commits on top is the standard workflow:

```shell
# Start editing on top of your feature bookmark
jj new your-feature

# Make fixes, then commit
jj diff
jj commit -m 'address pr comments'

# Move bookmark forward to include new commit
jj bookmark move your-feature --to @-

# Push (normal push, not force)
jj git push
```

### Rewriting Style (clean history)

For projects that prefer clean commits (force-push workflow):

```shell
# Edit the specific commit that needs fixing (trailing - = parent)
jj new your-feature-

# Make fixes, then squash into the parent
jj diff
jj squash

# Push — jj automatically force-pushes when history is rewritten
jj git push --bookmark your-feature
```

The `-` suffix is revset syntax: `your-feature-` means "parent of your-feature".

## Working with Others' Bookmarks

By default, `jj git fetch` doesn't import new remote bookmarks locally:

```shell
# Check out someone's branch without importing it
jj new feature-x@origin

# Or import all remote bookmarks automatically (in config):
# remotes.<name>.auto-track-bookmarks = "*"
```

With auto-tracking enabled, use `jj new feature-x` directly.

## Fork Workflow (Multiple Remotes)

### Initial Setup

```shell
jj git clone --remote upstream https://github.com/upstream-org/repo
cd repo
jj git remote add origin git@github.com:your-name/repo-fork
```

### Configure Fetch/Push Defaults

```shell
# Fetch from upstream (and optionally origin), push to fork
jj config set --repo git.fetch '["upstream", "origin"]'
jj config set --repo git.push origin

# Track main from both remotes
jj bookmark track main

# Set trunk to upstream so it's immutable
jj config set --repo 'revset-aliases."trunk()"' main@upstream
```

### Keeping Fork in Sync

```shell
jj git fetch  # fetches from configured remotes
jj git push --bookmark main  # pushes main to origin (your fork)
```

## Using GitHub CLI

For non-colocated repos, `gh` can't find the Git directory. Fix with `$GIT_DIR`:

```shell
# One-off
GIT_DIR=$(jj git root) gh pr create --title "My PR"

# Permanent fix: add to .envrc (requires direnv)
echo 'export GIT_DIR=$(jj git root)' >> .envrc
direnv allow
```

In colocated repos (`jj git init --colocate`), `gh` works without configuration.

## GitLab Push Options

Create merge requests and control CI directly from push:

```shell
# Skip CI
jj git push -o ci.skip

# Create merge request on push
jj git push --allow-new \
  -o merge_request.create \
  -o merge_request.target=main \
  -o 'merge_request.title=Add feature X' \
  -o merge_request.draft
```

## Useful Revsets for PR Workflows

```shell
# All local work not yet on any remote
jj log -r 'remote_bookmarks()..@'

# All your bookmarks not pushed to remote
jj log -r 'mine() & bookmarks() & ~remote_bookmarks()'

# Local bookmarks diverged from main
jj log -r 'bookmarks() & ~(main | remote_bookmarks())'

# All remote bookmarks you authored
jj log -r 'remote_bookmarks() & mine()'

# Commits on a specific bookmark not yet in main
jj log -r 'main..your-feature'
```
