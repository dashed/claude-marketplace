# fzf Integrations Reference

Recipes for integrating fzf with other tools.

## Table of Contents

- [ripgrep Integration](#ripgrep-integration)
- [fd Integration](#fd-integration)
- [bat Integration](#bat-integration)
- [Git Integration](#git-integration)
- [Docker Integration](#docker-integration)
- [Kubernetes Integration](#kubernetes-integration)
- [tmux Integration](#tmux-integration)
- [Shell Function Recipes](#shell-function-recipes)

## ripgrep Integration

### Basic Search with Preview

```bash
# Search and preview with syntax highlighting
rg --line-number --no-heading --color=always '' |
  fzf --ansi \
      --delimiter : \
      --preview 'bat --color=always {1} --highlight-line {2}' \
      --preview-window 'up,60%,border-bottom,+{2}+3/3,~3'
```

### Open Result in Editor

```bash
# Search and open in vim at matching line
rg --line-number --no-heading --color=always '' |
  fzf --ansi --delimiter : \
      --preview 'bat --color=always {1} --highlight-line {2}' \
      --bind 'enter:become(vim {1} +{2})'
```

### Interactive ripgrep (fzf as Frontend)

```bash
#!/usr/bin/env bash
# Save as 'rfv' and make executable

RG_PREFIX="rg --column --line-number --no-heading --color=always --smart-case"
INITIAL_QUERY="${*:-}"

fzf --ansi --disabled --query "$INITIAL_QUERY" \
    --bind "start:reload:$RG_PREFIX {q}" \
    --bind "change:reload:sleep 0.1; $RG_PREFIX {q} || true" \
    --delimiter : \
    --preview 'bat --color=always {1} --highlight-line {2}' \
    --preview-window 'up,60%,border-bottom,+{2}+3/3,~3' \
    --bind 'enter:become(vim {1} +{2})'
```

### Toggle Between ripgrep and fzf Mode

```bash
#!/usr/bin/env bash
# CTRL-R for ripgrep mode, CTRL-F for fzf mode

rm -f /tmp/rg-fzf-{r,f}
RG_PREFIX="rg --column --line-number --no-heading --color=always --smart-case"

fzf --ansi --disabled --query "${*:-}" \
    --bind "start:reload($RG_PREFIX {q})+unbind(ctrl-r)" \
    --bind "change:reload:sleep 0.1; $RG_PREFIX {q} || true" \
    --bind "ctrl-f:unbind(change,ctrl-f)+change-prompt(fzf> )+enable-search+rebind(ctrl-r)+transform-query(echo {q} > /tmp/rg-fzf-r; cat /tmp/rg-fzf-f)" \
    --bind "ctrl-r:unbind(ctrl-r)+change-prompt(rg> )+disable-search+reload($RG_PREFIX {q} || true)+rebind(change,ctrl-f)+transform-query(echo {q} > /tmp/rg-fzf-f; cat /tmp/rg-fzf-r)" \
    --prompt 'rg> ' \
    --delimiter : \
    --header 'CTRL-R (ripgrep) / CTRL-F (fzf)' \
    --preview 'bat --color=always {1} --highlight-line {2}' \
    --preview-window 'up,60%,border-bottom,+{2}+3/3,~3' \
    --bind 'enter:become(vim {1} +{2})'
```

## fd Integration

### File Search with Preview

```bash
# Find files with preview
fd --type f --hidden --follow --exclude .git |
  fzf --preview 'bat --color=always {}' \
      --bind 'enter:become(vim {})'
```

### Set as Default Command

```bash
# In ~/.bashrc or ~/.zshrc
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
```

### Toggle Files/Directories

```bash
fd --type f |
  fzf --prompt 'Files> ' \
      --header 'CTRL-D: Dirs / CTRL-F: Files' \
      --bind 'ctrl-d:change-prompt(Dirs> )+reload(fd --type d)' \
      --bind 'ctrl-f:change-prompt(Files> )+reload(fd --type f)'
```

### Filter by Extension

```bash
# Find Python files
fd --extension py | fzf --preview 'bat --color=always {}'

# Multiple extensions
fd --extension js --extension ts | fzf
```

## bat Integration

### Preview with Syntax Highlighting

```bash
fzf --preview 'bat --color=always --style=numbers --line-range :500 {}'
```

### Highlight Specific Line

```bash
# With line number from grep/rg
fzf --preview 'bat --color=always {1} --highlight-line {2}' --delimiter :
```

### Preview Window Settings

```bash
# Show first 500 lines with header
fzf --preview 'bat --color=always --style=header,numbers --line-range :500 {}'

# Plain output for speed
fzf --preview 'bat --color=always --style=plain {}'
```

## Git Integration

### Select Branches

```bash
# Checkout branch
git branch --all | fzf | xargs git checkout

# With preview of recent commits
git branch --all |
  fzf --preview 'git log --oneline -20 {}' |
  sed 's/^[* ]*//' | sed 's/remotes\/origin\///' |
  xargs git checkout
```

### Select Commits

```bash
# Copy commit hash
git log --oneline |
  fzf --preview 'git show --color=always {1}' |
  cut -d' ' -f1

# Interactive rebase from selected commit
git log --oneline |
  fzf --preview 'git show --color=always {1}' |
  cut -d' ' -f1 |
  xargs -I {} git rebase -i {}^
```

### Stage Files Interactively

```bash
# Select unstaged files to add
git status --short |
  fzf --multi --preview 'git diff --color=always {2}' |
  awk '{print $2}' |
  xargs git add
```

### View Changed Files

```bash
# Open changed files
git status --short |
  fzf --multi --preview 'git diff --color=always {2}' |
  awk '{print $2}' |
  xargs -o vim
```

### Stash Management

```bash
# Select and apply stash
git stash list |
  fzf --preview 'git stash show -p {1}' --delimiter : |
  cut -d: -f1 |
  xargs git stash apply
```

### fzf-git.sh Key Bindings

Highly recommended: [fzf-git.sh](https://github.com/junegunn/fzf-git.sh)

Provides keybindings:
- `CTRL-G CTRL-F` - Files from git status
- `CTRL-G CTRL-B` - Branches
- `CTRL-G CTRL-T` - Tags
- `CTRL-G CTRL-R` - Remotes
- `CTRL-G CTRL-H` - Commit hashes
- `CTRL-G CTRL-S` - Stashes
- `CTRL-G CTRL-L` - Reflogs
- `CTRL-G CTRL-W` - Worktrees
- `CTRL-G CTRL-E` - Each ref (git for-each-ref)

## Docker Integration

### Select Containers

```bash
# Attach to running container
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' |
  fzf --delimiter '\t' --with-nth 1,2,3 |
  cut -f1 |
  xargs -o docker attach
```

### Select Images

```bash
# Remove images
docker images --format '{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}' |
  fzf --multi --delimiter '\t' |
  cut -f2 |
  xargs docker rmi
```

### View Logs

```bash
# Follow container logs
docker ps --format '{{.Names}}' |
  fzf --preview 'docker logs --tail 50 {}' |
  xargs -o docker logs -f
```

## Kubernetes Integration

### Select Pods

```bash
# Get shell in pod
kubectl get pods --all-namespaces -o wide |
  fzf --header-lines=1 |
  awk '{print "-n", $1, $2}' |
  xargs -o kubectl exec -it -- /bin/sh
```

### Pod Logs with Follow

```bash
pods() {
  kubectl get pods --all-namespaces |
    fzf --info=inline --layout=reverse --header-lines=1 \
        --prompt "$(kubectl config current-context)> " \
        --header $'CTRL-O: logs | CTRL-R: reload\n' \
        --bind 'start,ctrl-r:reload:kubectl get pods --all-namespaces' \
        --bind 'ctrl-o:execute:kubectl logs --namespace {1} {2} | less' \
        --preview-window up:follow \
        --preview 'kubectl logs --follow --tail=100 --namespace {1} {2}'
}
```

### Context Switching

```bash
# Switch context
kubectl config get-contexts -o name |
  fzf --preview 'kubectl config view -o jsonpath="{.contexts[?(@.name==\"{}\")]}"' |
  xargs kubectl config use-context
```

## tmux Integration

### Select Sessions

```bash
# Attach to session
tmux list-sessions -F '#S' |
  fzf --preview 'tmux capture-pane -pt {}' |
  xargs tmux switch-client -t
```

### Select Windows

```bash
# Switch to window
tmux list-windows -a -F '#S:#W' |
  fzf --preview 'tmux capture-pane -pt {}' |
  xargs tmux switch-client -t
```

### tmux Popup

```bash
# Use fzf in tmux popup
fzf --tmux center,80%
```

## Shell Function Recipes

### Interactive cd

```bash
# cd with preview
fcd() {
  local dir
  dir=$(fd --type d --hidden --follow --exclude .git |
    fzf --preview 'tree -C {} | head -50') &&
  cd "$dir"
}
```

### Edit Recent Files

```bash
# Edit recent git files
vg() {
  local files
  files=$(git ls-files --modified --others --exclude-standard |
    fzf --multi --preview 'bat --color=always {}') &&
  vim $files
}
```

### Kill Process

```bash
# Interactive process killer
fkill() {
  local pid
  pid=$(ps -ef | sed 1d | fzf -m | awk '{print $2}')
  if [ -n "$pid" ]; then
    echo "$pid" | xargs kill -9
  fi
}
```

### Search History

```bash
# Enhanced history search
fh() {
  eval $(history | fzf +s --tac | sed 's/ *[0-9]* *//')
}
```

### Open GitHub PR

```bash
# Select and open PR
gpr() {
  gh pr list |
    fzf --preview 'gh pr view {1}' |
    awk '{print $1}' |
    xargs gh pr checkout
}
```

### Man Page Viewer

```bash
# Browse man pages
fman() {
  man -k . |
    fzf --prompt='Man> ' --preview 'man {1}' |
    awk '{print $1}' |
    xargs man
}
```

### Environment Variables

Add to your shell config:

```bash
# Better defaults
export FZF_DEFAULT_OPTS='
  --height 40%
  --layout reverse
  --border
  --info inline
  --preview-window right,50%,border-left
'

# CTRL-T with preview
export FZF_CTRL_T_OPTS="
  --preview 'bat --color=always --style=numbers --line-range :500 {}'
  --bind 'ctrl-/:change-preview-window(down|hidden|)'
"

# CTRL-R with preview
export FZF_CTRL_R_OPTS="
  --preview 'echo {}'
  --preview-window up:3:hidden:wrap
  --bind 'ctrl-/:toggle-preview'
  --bind 'ctrl-y:execute-silent(echo -n {2..} | pbcopy)+abort'
  --header 'CTRL-Y to copy'
"

# ALT-C with tree preview
export FZF_ALT_C_OPTS="
  --preview 'tree -C {} | head -100'
"
```

## Tips

### Performance

- Avoid `--ansi` in `FZF_DEFAULT_OPTS` (slows scanning)
- Use `--nth` sparingly (requires tokenization)
- Prefer string delimiter over regex
- Use `fd` instead of `find` for file listing

### Debugging

```bash
# Test preview command
echo "test.txt" | fzf --preview 'bat --color=always {}'

# See what fzf receives
fzf --preview 'echo {} | cat -v'
```

### Escaping

```bash
# Escape special characters in queries
fzf --query 'foo\ bar'  # Literal space

# In shell scripts, quote properly
fzf --bind "enter:execute(vim '{}')"
```
