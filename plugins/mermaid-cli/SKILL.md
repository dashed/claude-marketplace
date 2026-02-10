---
name: mermaid-cli
description: Generate, validate, and fix diagrams from Mermaid markup using the mermaid-cli (mmdc) tool. Use when creating flowcharts, sequence diagrams, class diagrams, state diagrams, ER diagrams, Gantt charts, pie charts, mindmaps, or any Mermaid-supported diagram type. Also use when validating, verifying, or fixing Mermaid diagram syntax. Triggers on mentions of mermaid, mmdc, diagram generation, diagram validation, or converting .mmd files to images/SVG/PDF.
---

# Mermaid CLI

## Overview

`mmdc` (Mermaid CLI) converts Mermaid diagram definitions into SVG, PNG, or PDF output. It is the official command-line interface for the Mermaid diagramming library, enabling text-based diagram generation without a browser.

Write diagram definitions in `.mmd` files using Mermaid's declarative syntax, then run `mmdc` to produce publication-ready output. This is the primary tool for generating diagrams from text in automated and scripting workflows.

`mmdc` also serves as a **syntax validator**: any render attempt validates the diagram. If the Mermaid syntax is invalid, mmdc exits with a non-zero code and reports parse errors to stderr. This enables iterative validate-and-fix workflows.

## Prerequisites

**CRITICAL**: Before proceeding, you MUST verify that mermaid-cli is installed:

```bash
mmdc --version
```

**If mmdc is not installed:**
- **DO NOT** attempt to install it automatically
- **STOP** and inform the user that mermaid-cli is required
- **RECOMMEND** manual installation with the following options:

```bash
# npm (global install)
npm install -g @mermaid-js/mermaid-cli

# npx (no install, run directly)
npx -p @mermaid-js/mermaid-cli mmdc --help

# Docker
docker pull minlag/mermaid-cli

# See https://github.com/mermaid-js/mermaid-cli for more options
```

**If mmdc is not available, exit gracefully and do not proceed with the workflow below.**

## Basic Workflow

### Step 1: Write the Diagram

Create a `.mmd` file with Mermaid syntax:

```bash
cat <<'EOF' > diagram.mmd
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action]
    B -->|No| D[End]
EOF
```

### Step 2: Generate Output

```bash
# Generate SVG (default, best for web)
mmdc -i diagram.mmd -o diagram.svg

# Generate PNG (raster image)
mmdc -i diagram.mmd -o diagram.png

# Generate PDF (document embedding)
mmdc -i diagram.mmd -o diagram.pdf
```

### Step 3: Verify

Check that the output file was created and is non-empty.

## Common Patterns

### Pattern 1: Generate SVG from File

The most common workflow. SVG is the default and recommended format.

```bash
mmdc -i flowchart.mmd -o flowchart.svg
```

### Pattern 2: Generate PNG with Theme and Background

Customize appearance with theme and background color.

```bash
# Dark theme with white background
mmdc -i diagram.mmd -o diagram.png -t dark -b white

# Forest theme with transparent background
mmdc -i diagram.mmd -o diagram.png -t forest -b transparent
```

### Pattern 3: Generate PDF with Fit-to-Page

Use `--pdfFit` to scale the diagram to fit the PDF page.

```bash
mmdc -i diagram.mmd -o diagram.pdf --pdfFit
```

### Pattern 4: Inline Diagram via Heredoc

Write and render a diagram in one step without a separate file. Useful for scripted/automated workflows.

```bash
# Write diagram to temp file and convert
cat <<'EOF' > /tmp/seq.mmd
sequenceDiagram
    Alice->>Bob: Hello Bob
    Bob-->>Alice: Hi Alice
    Alice->>Bob: How are you?
    Bob-->>Alice: Great!
EOF
mmdc -i /tmp/seq.mmd -o sequence.svg
```

### Pattern 5: Process Markdown File

Replace all `mermaid` code blocks in a Markdown file with generated images.

```bash
# Replace mermaid blocks with SVG images
mmdc -i README.md -o README-out.md

# Replace with PNG images
mmdc -i README.md -o README-out.md -e png
```

The output Markdown file will have each ` ```mermaid ` block replaced with an `<img>` tag pointing to the generated image file.

### Pattern 6: Custom Configuration

Apply a Mermaid configuration file for consistent styling.

```bash
# Create a config file
cat <<'EOF' > mermaid-config.json
{
  "theme": "forest",
  "flowchart": {
    "curve": "basis",
    "useMaxWidth": true
  }
}
EOF

# Use the config
mmdc -i diagram.mmd -o diagram.svg -c mermaid-config.json
```

### Pattern 7: Validate Diagram Syntax

Use mmdc to check if a `.mmd` file has valid Mermaid syntax. Any render attempt validates the diagram — if the syntax is invalid, mmdc exits with a non-zero code and prints parse errors to stderr.

```bash
# Validate by rendering to a temp file
mmdc -i diagram.mmd -o /tmp/_validate.svg -q 2>&1
echo "Exit code: $?"
# 0 = valid, non-zero = invalid (error details printed above)
rm -f /tmp/_validate.svg
```

### Pattern 8: Validate and Fix Workflow

Iteratively fix invalid Mermaid diagrams by rendering, reading errors, correcting syntax, and re-validating.

```bash
# Step 1: Attempt render to validate
mmdc -i diagram.mmd -o /tmp/_validate.svg -q 2>&1

# Step 2: If exit code is non-zero, read the error output
# Errors describe the syntax issue (e.g. "Parse error on line 3...")
# Fix the .mmd file based on the error messages

# Step 3: Re-validate after fixing
mmdc -i diagram.mmd -o /tmp/_validate.svg -q 2>&1

# Step 4: Once valid (exit code 0), generate final output
mmdc -i diagram.mmd -o diagram.svg
rm -f /tmp/_validate.svg
```

## Quick Reference

| Flag | Description | Example |
|------|-------------|---------|
| `-i <file>` | Input file (`.mmd` or `.md`) | `-i diagram.mmd` |
| `-o <file>` | Output file (format from extension) | `-o out.svg` |
| `-t <theme>` | Theme: default, forest, dark, neutral | `-t dark` |
| `-e <format>` | Output format override: svg, png, pdf | `-e png` |
| `-b <color>` | Background color | `-b transparent` |
| `-w <px>` | Width in pixels | `-w 1024` |
| `-H <px>` | Height in pixels | `-H 768` |
| `-s <factor>` | Scale factor (default: 1) | `-s 2` |
| `-c <file>` | Mermaid config JSON file | `-c config.json` |
| `-C <file>` | CSS file for styling | `-C custom.css` |
| `-p <file>` | Puppeteer config JSON file | `-p puppeteer.json` |
| `--pdfFit` | Fit diagram to PDF page | `--pdfFit` |
| `-q` | Quiet mode (suppress logs) | `-q` |
| `-I <id>` | SVG element id attribute | `-I my-diagram` |
| `--iconPacks` | Icon pack names (comma-separated) | `--iconPacks logos` |

## Supported Diagram Types

Mermaid supports a wide range of diagram types. Use the appropriate syntax in your `.mmd` file:

- **Flowchart** (`graph TD` / `graph LR` / `flowchart TD`)
- **Sequence Diagram** (`sequenceDiagram`)
- **Class Diagram** (`classDiagram`)
- **State Diagram** (`stateDiagram-v2`)
- **Entity Relationship** (`erDiagram`)
- **Gantt Chart** (`gantt`)
- **Pie Chart** (`pie`)
- **Mindmap** (`mindmap`)
- **Timeline** (`timeline`)
- **Git Graph** (`gitGraph`)
- **User Journey** (`journey`)
- **Sankey Diagram** (`sankey-beta`)
- **C4 Diagram** (`C4Context` / `C4Container` / `C4Component`)
- **Quadrant Chart** (`quadrantChart`)
- **XY Chart** (`xychart-beta`)
- **Block Diagram** (`block-beta`)
- **Architecture Diagram** (`architecture-beta`)
- **ZenUML** (`zenuml`)

See [Mermaid documentation](https://mermaid.js.org/intro/) for diagram syntax reference.

## Themes

Four built-in themes are available:

| Theme | Description |
|-------|-------------|
| `default` | Standard blue/gray palette |
| `forest` | Green-oriented natural colors |
| `dark` | Dark background with light text |
| `neutral` | Grayscale, suitable for printing |

```bash
mmdc -i diagram.mmd -o diagram.svg -t forest
```

For custom theming, use a configuration file with `themeVariables` or a CSS file with `-C`. See [references/configuration.md](references/configuration.md) for details.

## Advanced Usage

For comprehensive documentation beyond common workflows, see:

- [references/cli-reference.md](references/cli-reference.md) - Complete CLI flag reference with all options, detailed examples, and output format specifics
- [references/configuration.md](references/configuration.md) - Mermaid config, Puppeteer config, CSS customization, icon packs, layout engines, and theme variables

## Troubleshooting

**"mmdc: command not found"**
- mermaid-cli is not installed. See Prerequisites section for manual installation instructions
- Do NOT attempt automatic installation

**Chromium sandbox error on Linux**
- Create a Puppeteer config to disable the sandbox:

```bash
cat <<'EOF' > puppeteer-config.json
{
  "args": ["--no-sandbox", "--disable-setuid-sandbox"]
}
EOF
mmdc -i diagram.mmd -o diagram.svg -p puppeteer-config.json
```

**Docker permission errors**
- Run the Docker container with user flag:

```bash
docker run --rm -u $(id -u):$(id -g) -v $(pwd):/data minlag/mermaid-cli -i /data/diagram.mmd -o /data/diagram.svg
```

**Custom Chromium path**
- Set `executablePath` in a Puppeteer config file:

```bash
cat <<'EOF' > puppeteer-config.json
{
  "executablePath": "/usr/bin/chromium-browser"
}
EOF
mmdc -i diagram.mmd -o diagram.svg -p puppeteer-config.json
```

**Blank or empty output**
- Verify the `.mmd` file has valid Mermaid syntax
- Try running with verbose output (remove `-q` flag)
- Check that the diagram type keyword is correct (e.g., `graph`, `sequenceDiagram`)

**Timeout errors**
- Increase the Puppeteer timeout in a config file:

```bash
cat <<'EOF' > puppeteer-config.json
{
  "timeout": 60000
}
EOF
mmdc -i diagram.mmd -o diagram.svg -p puppeteer-config.json
```
