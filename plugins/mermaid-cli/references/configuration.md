# Configuration

Complete reference for configuring Mermaid CLI rendering, including Mermaid config files, Puppeteer config, CSS customization, icon packs, layout engines, and theme variables.

## Table of Contents

- [Mermaid Configuration File](#mermaid-configuration-file)
- [Per-Diagram-Type Options](#per-diagram-type-options)
- [Inline Directives](#inline-directives)
- [YAML Frontmatter in .mmd Files](#yaml-frontmatter-in-mmd-files)
- [Puppeteer Configuration](#puppeteer-configuration)
- [CSS Customization](#css-customization)
- [Icon Packs](#icon-packs)
- [Theme Variables](#theme-variables)
- [Layout Engines](#layout-engines)
- [Hand-Drawn Look](#hand-drawn-look)

## Mermaid Configuration File

Pass a JSON configuration file to mmdc with the `-c` flag:

```bash
mmdc -i diagram.mmd -o diagram.svg -c config.json
```

### Basic Structure

```json
{
  "theme": "default",
  "themeVariables": {},
  "themeCSS": "",
  "logLevel": "fatal",
  "securityLevel": "strict",
  "startOnLoad": false,
  "maxTextSize": 50000,
  "maxEdges": 500,
  "flowchart": {},
  "sequence": {},
  "gantt": {},
  "class": {},
  "state": {},
  "er": {},
  "pie": {},
  "mindmap": {}
}
```

### Top-Level Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `theme` | string | `"default"` | Theme name: default, forest, dark, neutral |
| `themeVariables` | object | `{}` | Override specific theme colors/values |
| `themeCSS` | string | `""` | Custom CSS injected into the diagram |
| `logLevel` | string | `"fatal"` | Log level: trace, debug, info, warn, error, fatal |
| `securityLevel` | string | `"strict"` | Security: strict, loose, antiscript, sandbox |
| `maxTextSize` | number | `50000` | Max characters in diagram text |
| `maxEdges` | number | `500` | Max edges in a diagram |
| `fontSize` | number | `16` | Base font size in pixels |
| `fontFamily` | string | `"trebuchet ms"` | Font family for diagram text |
| `htmlLabels` | boolean | `true` | Use HTML labels (better rendering) |
| `wrap` | boolean | `false` | Enable text wrapping |

### Example Config File

```json
{
  "theme": "forest",
  "themeVariables": {
    "primaryColor": "#4a90d9",
    "primaryTextColor": "#fff",
    "lineColor": "#333"
  },
  "flowchart": {
    "curve": "basis",
    "useMaxWidth": true,
    "htmlLabels": true
  },
  "sequence": {
    "actorMargin": 80,
    "showSequenceNumbers": true
  }
}
```

## Per-Diagram-Type Options

Each diagram type has its own configuration namespace.

### Flowchart

```json
{
  "flowchart": {
    "curve": "basis",
    "useMaxWidth": true,
    "htmlLabels": true,
    "diagramPadding": 8,
    "nodeSpacing": 50,
    "rankSpacing": 50,
    "defaultRenderer": "dagre-wrapper",
    "wrappingWidth": 200
  }
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `curve` | string | `"basis"` | Line curve: basis, linear, cardinal, step |
| `useMaxWidth` | boolean | `true` | Scale to container width |
| `htmlLabels` | boolean | `true` | Use HTML for labels |
| `diagramPadding` | number | `8` | Padding around diagram |
| `nodeSpacing` | number | `50` | Spacing between nodes |
| `rankSpacing` | number | `50` | Spacing between ranks |
| `wrappingWidth` | number | `200` | Max width before text wraps |

### Sequence Diagram

```json
{
  "sequence": {
    "actorMargin": 50,
    "actorFontSize": 14,
    "actorFontWeight": 400,
    "noteFontSize": 14,
    "messageFontSize": 16,
    "showSequenceNumbers": false,
    "useMaxWidth": true,
    "width": 150,
    "height": 65,
    "boxMargin": 10,
    "boxTextMargin": 5,
    "noteMargin": 10,
    "messageMargin": 35,
    "mirrorActors": true,
    "bottomMarginAdj": 1,
    "rightAngles": false,
    "wrap": false
  }
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `actorMargin` | number | `50` | Margin between actors |
| `showSequenceNumbers` | boolean | `false` | Show message sequence numbers |
| `mirrorActors` | boolean | `true` | Show actors at bottom too |
| `rightAngles` | boolean | `false` | Use right-angle message lines |
| `wrap` | boolean | `false` | Wrap long messages |
| `width` | number | `150` | Actor box width |
| `height` | number | `65` | Actor box height |

### Entity Relationship (ER) Diagram

```json
{
  "er": {
    "diagramPadding": 20,
    "layoutDirection": "TB",
    "minEntityWidth": 100,
    "minEntityHeight": 75,
    "entityPadding": 15,
    "stroke": "gray",
    "fill": "honeydew",
    "fontSize": 12,
    "useMaxWidth": true
  }
}
```

### Gantt Chart

```json
{
  "gantt": {
    "titleTopMargin": 25,
    "barHeight": 20,
    "barGap": 4,
    "topPadding": 50,
    "leftPadding": 75,
    "gridLineStartPadding": 35,
    "fontSize": 11,
    "sectionFontSize": 11,
    "numberSectionStyles": 4,
    "axisFormat": "%Y-%m-%d",
    "tickInterval": "1week",
    "useMaxWidth": true
  }
}
```

### Class Diagram

```json
{
  "class": {
    "arrowMarkerAbsolute": false,
    "useMaxWidth": true,
    "defaultRenderer": "dagre-wrapper"
  }
}
```

### State Diagram

```json
{
  "state": {
    "dividerMargin": 10,
    "sizeUnit": 5,
    "padding": 8,
    "textHeight": 10,
    "titleShift": -15,
    "noteMargin": 10,
    "forkWidth": 70,
    "forkHeight": 7,
    "miniPadding": 2,
    "defaultRenderer": "dagre-wrapper",
    "useMaxWidth": true
  }
}
```

### Pie Chart

```json
{
  "pie": {
    "useMaxWidth": true,
    "textPosition": 0.75,
    "useWidth": 960
  }
}
```

### Mindmap

```json
{
  "mindmap": {
    "useMaxWidth": true,
    "padding": 10,
    "maxNodeWidth": 200
  }
}
```

## Inline Directives

Override configuration inline within `.mmd` files using the `%%{init: ...}%%` directive at the top of the diagram:

```
%%{init: {"theme": "dark", "flowchart": {"curve": "linear"}}}%%
graph TD
    A --> B --> C
```

### Examples

```
%%{init: {"theme": "forest"}}%%
sequenceDiagram
    Alice->>Bob: Hello

%%{init: {"theme": "neutral", "sequence": {"showSequenceNumbers": true}}}%%
sequenceDiagram
    Alice->>Bob: Message 1
    Bob-->>Alice: Reply

%%{init: {"themeVariables": {"primaryColor": "#ff6347"}}}%%
graph LR
    A[Red Node] --> B[Another Node]
```

Inline directives override values from the config file (`-c`), allowing per-diagram customization.

## YAML Frontmatter in .mmd Files

Mermaid files can include YAML frontmatter for configuration:

```yaml
---
title: My Diagram
config:
  theme: dark
  flowchart:
    curve: basis
---
graph TD
    A --> B --> C
```

The `config` key in frontmatter accepts the same options as the JSON config file. Frontmatter is processed before inline directives.

### Priority Order

Configuration is merged in this priority order (highest wins):

1. Inline directives (`%%{init: ...}%%`)
2. YAML frontmatter (`config:`)
3. Config file (`-c`)
4. CLI flags (`-t` theme)
5. Defaults

## Puppeteer Configuration

Puppeteer is the headless Chromium engine used by mmdc for rendering. Configure it with `-p`:

```bash
mmdc -i diagram.mmd -o diagram.svg -p puppeteer-config.json
```

### Config File Format

```json
{
  "executablePath": "/usr/bin/chromium-browser",
  "args": ["--no-sandbox", "--disable-setuid-sandbox"],
  "headless": true,
  "timeout": 30000
}
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `executablePath` | string | (bundled) | Path to Chromium/Chrome binary |
| `args` | string[] | `[]` | Additional Chromium arguments |
| `headless` | boolean | `true` | Run in headless mode |
| `timeout` | number | `30000` | Navigation timeout in ms |

### Common Scenarios

**Linux without sandbox (CI/Docker):**
```json
{
  "args": ["--no-sandbox", "--disable-setuid-sandbox"]
}
```

**Custom Chromium installation:**
```json
{
  "executablePath": "/opt/google/chrome/chrome"
}
```

**Large diagram timeout:**
```json
{
  "timeout": 120000
}
```

**Docker environment:**
```json
{
  "executablePath": "/usr/bin/chromium-browser",
  "args": [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage"
  ]
}
```

## CSS Customization

Apply custom CSS to diagrams using the `-C` flag or `themeCSS` config option.

### Using a CSS File (`-C`)

```bash
mmdc -i diagram.mmd -o diagram.svg -C custom.css
```

**Example `custom.css`:**
```css
/* Style all nodes */
.node rect {
  fill: #4a90d9;
  stroke: #2c5282;
  stroke-width: 2px;
  rx: 8px;
}

/* Style node labels */
.node .label {
  color: white;
  font-weight: bold;
}

/* Style edges */
.edgePath path {
  stroke: #666;
  stroke-width: 2px;
}

/* Style edge labels */
.edgeLabel {
  background-color: #fff;
  padding: 2px 4px;
}
```

### Using themeCSS in Config

```json
{
  "themeCSS": ".node rect { fill: #4a90d9; } .edgePath path { stroke: #666; }"
}
```

The CSS is injected into the SVG and applies to the rendered diagram elements. CSS selectors vary by diagram type.

## Icon Packs

Icon packs add icons to architecture and other diagrams.

### Built-in Icon Packs

Use `--iconPacks` to load named icon packs:

```bash
mmdc -i arch.mmd -o arch.svg --iconPacks logos
```

### Custom Icon Packs

Use `--iconPacksNamesAndUrls` for custom icon sources:

```bash
mmdc -i arch.mmd -o arch.svg --iconPacksNamesAndUrls '{"myicons": "https://example.com/icons.json"}'
```

### Usage in Diagrams

```
architecture-beta
    group api(logos:aws-lambda)[API Layer]
    service web(logos:react)[Frontend]
    service server(logos:nodejs)[Backend]

    web:R --> L:server
```

Icon packs are primarily used with architecture diagrams (`architecture-beta`).

## Theme Variables

Customize theme colors by setting `themeVariables` in the config file:

```json
{
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#4a90d9",
    "primaryTextColor": "#ffffff",
    "primaryBorderColor": "#2c5282",
    "secondaryColor": "#48bb78",
    "tertiaryColor": "#ed8936",
    "lineColor": "#333333",
    "textColor": "#333333",
    "mainBkg": "#ffffff",
    "nodeBorder": "#333333",
    "clusterBkg": "#f7fafc",
    "clusterBorder": "#cbd5e0",
    "titleColor": "#333333",
    "edgeLabelBackground": "#ffffff",
    "noteTextColor": "#333333",
    "noteBkgColor": "#ffffcc",
    "noteBorderColor": "#cccc00"
  }
}
```

### Key Theme Variables

| Variable | Description |
|----------|-------------|
| `primaryColor` | Main node/shape fill color |
| `primaryTextColor` | Text color on primary elements |
| `primaryBorderColor` | Border color of primary elements |
| `secondaryColor` | Secondary element fill |
| `tertiaryColor` | Tertiary element fill |
| `lineColor` | Edge/line color |
| `textColor` | General text color |
| `mainBkg` | Main background color |
| `nodeBorder` | Default node border color |
| `clusterBkg` | Subgraph/cluster background |
| `clusterBorder` | Subgraph/cluster border |
| `noteBkgColor` | Note background color |
| `noteBorderColor` | Note border color |

Use `"theme": "base"` as the starting theme when customizing with `themeVariables` for maximum control.

## Layout Engines

Mermaid supports multiple layout engines for flowcharts and other directed graph diagrams.

### Dagre (Default)

The default layout engine. Good for most use cases.

```json
{
  "flowchart": {
    "defaultRenderer": "dagre-wrapper"
  }
}
```

### ELK (Eclipse Layout Kernel)

Alternative layout engine that can produce better results for complex diagrams. Must be enabled via config.

```json
{
  "flowchart": {
    "defaultRenderer": "elk"
  }
}
```

Or use the `elk` keyword in the diagram:

```
%%{init: {"flowchart": {"defaultRenderer": "elk"}}}%%
graph TD
    A --> B
    A --> C
    B --> D
    C --> D
```

**When to use ELK:**
- Complex diagrams with many crossing edges
- Large diagrams where dagre produces cluttered output
- When you need more control over edge routing

**Note:** ELK support may require a specific Mermaid version. Check compatibility.

## Hand-Drawn Look

Mermaid supports a hand-drawn (sketchy) rendering style using the `look` config option:

```json
{
  "look": "handDrawn",
  "theme": "default"
}
```

Or via inline directive:

```
%%{init: {"look": "handDrawn"}}%%
graph TD
    A[Design] --> B[Implement]
    B --> C[Test]
    C --> D[Deploy]
```

The hand-drawn look applies a sketch-like visual style to shapes and lines, useful for informal diagrams, wireframes, or draft visualizations.

### Combining with Themes

```json
{
  "look": "handDrawn",
  "theme": "neutral"
}
```

The hand-drawn look works with all themes and diagram types, though results may vary.
