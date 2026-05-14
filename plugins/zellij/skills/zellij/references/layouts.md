# Zellij Layouts Reference

Layouts define the arrangement of panes and tabs when starting zellij.

## Table of Contents

- [Using Layouts](#using-layouts)
- [Layout Format (KDL)](#layout-format-kdl)
- [Basic Examples](#basic-examples)
- [Pane Configuration](#pane-configuration)
- [Tab Configuration](#tab-configuration)
- [Floating Panes](#floating-panes)
- [Templates](#templates)
- [Built-in Layouts](#built-in-layouts)

## Using Layouts

```bash
# Start with a layout file
zellij --layout /path/to/my-layout.kdl

# Start with built-in layout
zellij --layout compact
zellij --layout default

# Add layout to existing session as new tab
zellij action new-tab --layout /path/to/layout.kdl

# Dump current layout
zellij action dump-layout > saved-layout.kdl
```

## Layout Format (KDL)

Zellij uses [KDL](https://kdl.dev/) format for layouts. Basic structure:

```kdl
layout {
    // Tab definitions go here
    tab {
        // Pane definitions go here
        pane
    }
}
```

## Basic Examples

### Single Pane

```kdl
layout {
    pane
}
```

### Two Panes (Horizontal Split)

```kdl
layout {
    pane split_direction="vertical" {
        pane
        pane
    }
}
```

### Two Panes (Vertical Split)

```kdl
layout {
    pane split_direction="horizontal" {
        pane
        pane
    }
}
```

### Three Panes (IDE-like)

```kdl
layout {
    pane split_direction="vertical" {
        pane size="20%"
        pane split_direction="horizontal" {
            pane
            pane size="30%"
        }
    }
}
```

### Multiple Tabs

```kdl
layout {
    tab name="main" {
        pane
    }
    tab name="servers" {
        pane split_direction="horizontal" {
            pane command="htop"
            pane command="tail" {
                args "-f" "/var/log/syslog"
            }
        }
    }
}
```

## Pane Configuration

### Size

```kdl
pane size="50%"      // Percentage
pane size=20         // Fixed rows/columns
```

### Commands

```kdl
// Run a command
pane command="htop"

// Command with arguments
pane command="tail" {
    args "-f" "/var/log/syslog"
}

// Command with working directory
pane command="npm" cwd="/path/to/project" {
    args "run" "dev"
}
```

### Name and Focus

```kdl
pane name="editor" focus=true
```

### Start Suspended

```kdl
// Command doesn't run until Enter is pressed
pane command="long-running-task" start_suspended=true
```

### Close on Exit

```kdl
pane command="ls" close_on_exit=true
```

### Borderless

```kdl
pane borderless=true
```

### Edit Mode

```kdl
// Open file in $EDITOR
pane edit="/path/to/file.txt"
pane edit="/path/to/file.txt" line_number=42
```

## Tab Configuration

### Basic Tab

```kdl
tab name="my-tab" {
    pane
}
```

### Tab with Working Directory

```kdl
tab name="project" cwd="/path/to/project" {
    pane
}
```

### Focused Tab

```kdl
tab name="main" focus=true {
    pane
}
```

## Floating Panes

### Define Floating Panes

```kdl
layout {
    pane

    floating_panes {
        pane command="htop" {
            x 10
            y 10
            width "50%"
            height "50%"
        }
    }
}
```

### Floating Pane Options

```kdl
floating_panes {
    pane {
        x "10%"           // Position from left
        y "10%"           // Position from top
        width "80%"       // Width
        height "80%"      // Height
        pinned true       // Always on top
    }
}
```

## Templates

Templates allow reusable layout definitions.

### Defining Templates

```kdl
layout {
    // Define a template
    pane_template name="shell" {
        command "zsh"
    }

    pane_template name="editor" {
        command "nvim"
    }

    // Use templates
    tab {
        shell
        editor focus=true
    }
}
```

### Tab Templates

```kdl
layout {
    tab_template name="dev-tab" {
        pane split_direction="vertical" {
            pane size="30%" command="nvim"
            pane
        }
    }

    // Use tab template
    dev-tab name="frontend" cwd="/path/to/frontend"
    dev-tab name="backend" cwd="/path/to/backend"
}
```

### Default Tab Template

```kdl
layout {
    // Applied to tabs without explicit template
    default_tab_template {
        pane size=1 borderless=true {
            plugin location="zellij:tab-bar"
        }
        children    // Where tab content goes
        pane size=2 borderless=true {
            plugin location="zellij:status-bar"
        }
    }

    tab name="main" {
        pane
    }
}
```

## Built-in Layouts

### default

Standard layout with tab bar and status bar.

```bash
zellij --layout default
```

### compact

Minimal layout with compact bar (less vertical space).

```bash
zellij --layout compact
```

### disable-status-bar

No status bar or tab bar.

```bash
zellij --layout disable-status-bar
```

## Plugins in Layouts

### Built-in Plugins

```kdl
layout {
    pane size=1 borderless=true {
        plugin location="zellij:tab-bar"
    }
    pane
    pane size=2 borderless=true {
        plugin location="zellij:status-bar"
    }
}
```

### File Browser (Strider)

```kdl
layout {
    pane split_direction="vertical" {
        pane size="20%" {
            plugin location="zellij:strider"
        }
        pane
    }
}
```

### Custom Plugins

```kdl
pane {
    plugin location="file:/path/to/plugin.wasm" {
        config_key "config_value"
    }
}
```

## Layout Directory

Default layout directories:

- Linux: `~/.config/zellij/layouts/`
- macOS: `~/Library/Application Support/org.Zellij-Contributors.Zellij/layouts/`

Place `.kdl` files here to use by name:

```bash
# Uses ~/.config/zellij/layouts/my-dev.kdl
zellij --layout my-dev
```

## Complex Example

Full IDE-like development layout:

```kdl
layout {
    default_tab_template {
        pane size=1 borderless=true {
            plugin location="zellij:tab-bar"
        }
        children
        pane size=2 borderless=true {
            plugin location="zellij:status-bar"
        }
    }

    tab name="code" focus=true {
        pane split_direction="vertical" {
            pane size="20%" {
                plugin location="zellij:strider"
            }
            pane split_direction="horizontal" {
                pane name="editor" focus=true
                pane size="30%" name="terminal"
            }
        }
    }

    tab name="servers" {
        pane split_direction="horizontal" {
            pane command="npm" cwd="/path/to/frontend" {
                args "run" "dev"
            }
            pane command="npm" cwd="/path/to/backend" {
                args "run" "start"
            }
        }
    }

    tab name="logs" {
        pane command="tail" {
            args "-f" "/var/log/app.log"
        }
    }
}
```

## Converting from YAML

Older zellij versions used YAML. Convert with:

```bash
zellij convert-layout old-layout.yaml > new-layout.kdl
```
