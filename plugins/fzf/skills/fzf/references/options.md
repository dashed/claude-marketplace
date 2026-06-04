# fzf Options Reference

Complete reference for all fzf command-line options.

> **Version annotations:** Flags marked `(fzf X.Y+)` require at least that fzf version; unmarked flags are long-standing basics. For the consolidated feature→version lookup (and removed/changed defaults), see [references/version-features.md](version-features.md). This reference is documented against fzf 0.73.x — confirm on your system with `fzf --version`.

## Table of Contents

- [Search Options](#search-options)
- [Input/Output Options](#inputoutput-options)
- [Display Mode Options](#display-mode-options)
- [Layout Options](#layout-options)
- [List Section Options](#list-section-options)
- [Input Section Options](#input-section-options)
- [Preview Options](#preview-options)
- [Header/Footer Options](#headerfooter-options)
- [Scripting Options](#scripting-options)
- [Directory Walker Options](#directory-walker-options)
- [History Options](#history-options)
- [Color Options](#color-options)
- [Shell Integration](#shell-integration)

## Search Options

### Mode Selection

| Option | Description |
|--------|-------------|
| `-x, --extended` | Extended search mode (default) |
| `+x, --no-extended` | Disable extended search |
| `-e, --exact` | Exact match mode |
| `-i, --ignore-case` | Case-insensitive search |
| `+i, --no-ignore-case` | Case-sensitive search |
| `--smart-case` | Smart case (default) |
| `--literal` | Don't normalize latin characters |

### Algorithm

| Option | Description |
|--------|-------------|
| `--scheme=SCHEME` | Scoring scheme: `default`, `path` (fzf 0.59+), `history` |
| `--algo=TYPE` | Algorithm: `v2` (quality), `v1` (speed) |

### Field Processing

| Option | Description |
|--------|-------------|
| `-d, --delimiter=STR` | Field delimiter (regex or string) |
| `-n, --nth=N[,..]` | Limit search to specific fields |
| `--with-nth=N[,..]` | Transform display (field expressions) |
| `--accept-nth=N[,..]` | Fields to print on accept |

### Sorting

| Option | Description |
|--------|-------------|
| `+s, --no-sort` | Don't sort results |
| `--tiebreak=CRI[,..]` | Tiebreak criteria |

**Tiebreak criteria:**
- `length` - Shorter line preferred (default)
- `chunk` - Shorter matched chunk
- `pathname` - Match in filename preferred (fzf 0.59+)
- `begin` - Match closer to beginning
- `end` - Match closer to end
- `index` - Earlier in input (implicit last)

### Other Search Options

| Option | Description |
|--------|-------------|
| `--disabled` | Disable search (selector mode) |
| `--tail=NUM` | Limit items in memory |

## Input/Output Options

| Option | Description |
|--------|-------------|
| `--read0` | NUL-delimited input |
| `--print0` | NUL-delimited output |
| `--ansi` | Process ANSI color codes |
| `--sync` | Synchronous search |
| `--no-tty-default` | Use stderr for TTY detection |

## Display Mode Options

### Height Mode

```bash
fzf --height=HEIGHT[%]    # Fixed height
fzf --height=~HEIGHT[%]   # Adaptive height (shrinks for small lists)
fzf --height=-N           # Terminal height minus N
```

| Option | Description |
|--------|-------------|
| `--height=HEIGHT[%]` | Non-fullscreen mode |
| `--min-height=HEIGHT[+]` | Minimum height (with percentage height) |

### Popup Mode (tmux / Zellij)

```bash
fzf --popup [center|top|bottom|left|right][,SIZE[%]][,SIZE[%]][,border-native]
```

`--popup` (fzf 0.71+) opens fzf in a tmux popup **or** a Zellij floating pane — requires **tmux 3.3+** or **Zellij 0.44+**. Add `border-native` to use the multiplexer's own popup border instead of fzf's.

`--tmux` (fzf 0.53+) is the older flag; as of fzf 0.71 it is a **back-compat alias for `--popup`** (same behavior, also targets Zellij). Prefer `--popup` in new scripts.

Examples:
```bash
fzf --popup center            # Center, 50%
fzf --popup 80%               # Center, 80%
fzf --popup left,40%          # Left side, 40% width
fzf --popup bottom,30%        # Bottom, 30% height
fzf --popup top,80%,40%       # Top, 80% width, 40% height
fzf --popup center,border-native  # Use the multiplexer's popup border
```

## Layout Options

| Option | Description |
|--------|-------------|
| `--layout=LAYOUT` | `default`, `reverse`, `reverse-list` |
| `--reverse` | Alias for `--layout=reverse` |
| `--margin=MARGIN` | Margin around finder |
| `--padding=PADDING` | Padding inside border |

### Border Options

| Option | Description |
|--------|-------------|
| `--border[=STYLE]` | Draw border around finder |
| `--border-label=LABEL` | Label on border |
| `--border-label-pos=N[:pos]` | Label position |

**Border styles:**
`rounded`, `sharp`, `bold`, `double`, `block`, `thinblock`, `dashed` (fzf 0.72+), `horizontal`, `vertical`, `line`, `top`, `bottom`, `left`, `right`, `none`

(Applies to all border flags: `--border`, `--list-border`, `--input-border`, `--header-border`, `--footer-border`, `--preview-border`.)

## List Section Options

### Selection

| Option | Description |
|--------|-------------|
| `-m, --multi[=MAX]` | Enable multi-select (optional limit) |
| `+m, --no-multi` | Disable multi-select |

### Display

| Option | Description |
|--------|-------------|
| `--highlight-line` | Highlight entire current line |
| `--cycle` | Enable cyclic scroll |
| `--wrap` | Enable line wrap (char-level) (fzf 0.54+) |
| `--wrap=word`, `--wrap-word` | Word-level line wrap (fzf 0.68+) |
| `--wrap-sign=STR` | Indicator for wrapped lines (fzf 0.54+) |
| `--no-multi-line` | Disable multi-line items |
| `--raw` | Show non-matching items (dimmed) (fzf 0.66+) |
| `--tac` | Reverse input order |
| `--track` | Track current selection |

### Scrolling

| Option | Description |
|--------|-------------|
| `--scroll-off=LINES` | Lines to keep visible at edges |
| `--no-hscroll` | Disable horizontal scroll |
| `--hscroll-off=COLS` | Columns to keep visible |

### Markers

| Option | Description |
|--------|-------------|
| `--pointer=STR` | Pointer character |
| `--marker=STR` | Selection marker |
| `--marker-multi-line=STR` | Multi-line marker (3 chars) |
| `--ellipsis=STR` | Truncation indicator |
| `--scrollbar=CHAR[CHAR]` | Scrollbar characters |
| `--no-scrollbar` | Disable scrollbar |

### Gap and Freeze

| Option | Description |
|--------|-------------|
| `--gap[=N]` | Empty lines between items |
| `--gap-line[=STR]` | Line character for gaps |
| `--freeze-left=N` | Freeze N left fields (fzf 0.67+) |
| `--freeze-right=N` | Freeze N right fields (fzf 0.67+) |
| `--keep-right` | Keep right end visible |

### List Border

| Option | Description |
|--------|-------------|
| `--list-border[=STYLE]` | Border around list (fzf 0.58+) |
| `--list-label=LABEL` | List border label |
| `--list-label-pos=N[:pos]` | Label position |

## Input Section Options

| Option | Description |
|--------|-------------|
| `--prompt=STR` | Input prompt (default: `> `) |
| `--info=STYLE` | Info display style |
| `--info-command=CMD` | Custom info generator |
| `--no-info` | Hide info line |
| `--no-input` | Hide input section |
| `--ghost=TEXT` | Ghost text when empty (fzf 0.61+) |
| `--filepath-word` | Path-aware word movements |
| `--separator=STR` | Separator line character |
| `--no-separator` | Hide separator |

**Info styles:**
`default`, `right`, `hidden`, `inline`, `inline:PREFIX`, `inline-right`, `inline-right:PREFIX`

### Input Border

| Option | Description |
|--------|-------------|
| `--input-border[=STYLE]` | Border around input (fzf 0.58+) |
| `--input-label=LABEL` | Input border label |
| `--input-label-pos=N[:pos]` | Label position |

## Preview Options

### Preview Command

```bash
fzf --preview='COMMAND'
```

**Placeholders:**
- `{}` - Current item (quoted)
- `{+}` - Selected items (space-separated)
- `{q}` - Query string
- `{n}` - Zero-based index
- `{1}`, `{2}`, etc. - Nth field
- `{-1}` - Last field
- `{1..3}` - Fields 1-3
- `{2..}` - Fields 2 to end

**Flags:**
- `{+}` - All selected
- `{f}` - Write to temp file
- `{r}` - Raw (unquoted)
- `{s}` - Preserve whitespace

### Preview Window

```bash
fzf --preview-window=OPTS
```

**Position:** `up`, `down`, `left`, `right` (default: right), `next` (fzf 0.73+ — adjacent to the input section, on the list side: above the input by default, below it with `--layout=reverse`)

**Options:**
- `SIZE[%]` - Window size
- `border-STYLE` - Border style
- `wrap` / `nowrap` - Line wrapping
- `follow` / `nofollow` - Auto-scroll
- `cycle` / `nocycle` - Cyclic scroll
- `info` / `noinfo` - Show scroll info
- `hidden` - Start hidden
- `+SCROLL[/DENOM]` - Initial scroll offset
- `~HEADER_LINES` - Fixed header lines
- `default` - Reset to defaults
- `<SIZE(ALTERNATIVE)` - Responsive layout

Example:
```bash
fzf --preview-window='right,50%,border-left,+{2}+3/3,~3'
```

### Preview Labels

| Option | Description |
|--------|-------------|
| `--preview-border[=STYLE]` | Preview border style |
| `--preview-label=LABEL` | Preview label |
| `--preview-label-pos=N[:pos]` | Label position |
| `--preview-wrap-sign=STR` | Indicator for wrapped lines in the preview (fzf 0.68+) |

## Header/Footer Options

### Header

| Option | Description |
|--------|-------------|
| `--header=STR` | Sticky header text |
| `--header-lines=N` | First N lines as header |
| `--header-first` | Header before prompt |
| `--header-border[=STYLE]` | Header border (fzf 0.58+) |
| `--header-label=LABEL` | Header label |
| `--header-lines-border[=STYLE]` | Separate header lines (fzf 0.59+) |

### Footer

| Option | Description |
|--------|-------------|
| `--footer=STR` | Sticky footer text (fzf 0.63+) |
| `--footer-border[=STYLE]` | Footer border (fzf 0.63+) |
| `--footer-label=LABEL` | Footer label (fzf 0.63+) |

## Scripting Options

| Option | Description |
|--------|-------------|
| `-q, --query=STR` | Initial query string |
| `-1, --select-1` | Auto-select if single match |
| `-0, --exit-0` | Exit if no match |
| `-f, --filter=STR` | Filter mode (non-interactive) |
| `--print-query` | Print query as first line |
| `--expect=KEYS` | Print key pressed as first line |
| `--no-clear` | Don't clear screen on exit |

## Directory Walker Options

When `FZF_DEFAULT_COMMAND` is not set:

| Option | Description |
|--------|-------------|
| `--walker=[file][,dir][,follow][,hidden]` | Walker behavior |
| `--walker-root=DIR [...]` | Starting directories |
| `--walker-skip=DIRS` | Directories to skip |

Default: `--walker=file,follow,hidden`
Default skip: `.git,node_modules`

## History Options

| Option | Description |
|--------|-------------|
| `--history=FILE` | History file path |
| `--history-size=N` | Max history entries (default: 1000) |

## Color Options

### Base Schemes

```bash
fzf --color=BASE_SCHEME
```

- `dark` - Dark terminal (default on 256-color)
- `light` - Light terminal
- `base16` / `16` - Base 16 colors
- `bw` - No colors

### Style Presets

```bash
fzf --style=PRESET    # fzf 0.58+
```

Presets: `default`, `minimal`, `full[:BORDER_STYLE]`

### Color Names

**Text colors:**
`fg`, `bg`, `hl`, `fg+` (current), `bg+`, `hl+`, `preview-fg`, `preview-bg`

**UI colors:**
`info`, `prompt`, `pointer`, `marker`, `spinner`, `header`, `border`, `label`, `query`, `disabled`, `separator`, `scrollbar`

**Specialized:**
`selected-fg`, `selected-bg`, `selected-hl`, `gutter`, `nth`, `ghost`

### ANSI Colors

- `-1` - Default/original color
- `0-15` - Base colors (black, red, green, yellow, blue, magenta, cyan, white, bright-*)
- `16-255` - 256 colors
- `#rrggbb` - 24-bit colors

### Attributes

`regular`, `bold`, `underline`, `reverse`, `dim`, `italic`, `strikethrough`, `strip`

Example:
```bash
fzf --color='fg:#d0d0d0,bg:#121212,hl:#5f87af' \
    --color='fg+:#d0d0d0,bg+:#262626,hl+:#5fd7ff' \
    --color='info:#afaf87,prompt:#d7005f,pointer:#af5fff'
```

## Shell Integration

| Option | Description |
|--------|-------------|
| `--bash` | Print bash integration script (fzf 0.48+) |
| `--zsh` | Print zsh integration script (fzf 0.48+) |
| `--fish` | Print fish integration script (fzf 0.48+, requires fish 3.4.0+ as of fzf 0.71) |
| `--nushell` | Print Nushell integration script (fzf 0.73+) |

## Advanced Options

| Option | Description |
|--------|-------------|
| `--bind=BINDINGS` | Custom key/event bindings |
| `--with-shell=STR` | Shell for commands |
| `--listen[=ADDR:PORT]` | Start HTTP server |
| `--listen-unsafe[=ADDR:PORT]` | Allow remote execution |
| `--jump-labels=CHARS` | Characters for jump mode |
| `--tabstop=N` | Tab width (default: 8) |
| `--gutter=CHAR` | Gutter column character (fzf 0.66+) |
| `--gutter-raw=CHAR` | Gutter character in raw mode; pairs with `--raw` (fzf 0.66+) |
| `--id-nth=N[,..]` | Item identity fields for cross-reload tracking; use with `--track` to keep the cursor on the same item across `reload` (fzf 0.71+) |

## Other Options

| Option | Description |
|--------|-------------|
| `--no-mouse` | Disable mouse |
| `--no-unicode` | Use ASCII characters |
| `--no-bold` | Don't use bold text |
| `--black` | Use black background |
| `--ambidouble` | Double-width ambiguous chars |
| `--version` | Show version |
| `--help` | Show help |
| `--man` | Show man page |
