# Coordinate System Reference

## Overview

The `shot` command captures the viewport at the device's native resolution. The screenshot image dimensions differ from CSS pixel dimensions by the Device Pixel Ratio (DPR).

## Key Formula

```
CSS pixels = screenshot image pixels / DPR
```

CDP Input events (`clickxy`, mouse dispatch) always take **CSS pixels**, not image pixels.

## Device Pixel Ratio (DPR)

The DPR is the ratio between physical/image pixels and CSS pixels:

| Display Type | Typical DPR | Conversion |
|---|---|---|
| Standard (1080p) | 1 | CSS px = image px |
| Retina / HiDPI | 2 | CSS px = image px / 2 |
| Some 4K displays | 3 | CSS px = image px / 3 |

The `shot` command prints the detected DPR and an example conversion for the current page.

## DPR Detection

The CLI detects DPR in this order:

1. `Page.getLayoutMetrics` — compares visual viewport to CSS viewport
2. `Emulation.getDeviceMetricsOverride` — checks for emulated DPR
3. `window.devicePixelRatio` — JavaScript fallback

## Worked Example

On a Retina display (DPR=2), you take a screenshot and want to click a button visible at image coordinates (400, 600):

```
CSS x = 400 / 2 = 200
CSS y = 600 / 2 = 300
```

```bash
python -m chrome_cdp clickxy <target> 200 300
```

## Viewer Scaling

If your image viewer rescales the screenshot (e.g., fits to window), you need to account for that additional scaling:

```
CSS px = (viewer pixel coordinate / viewer scale factor) / DPR
```

The `shot` output gives the DPR directly — you only need to know the viewer's own scaling to compute the final CSS coordinates.

## Coordinate Tips

- Always use `shot` output to get the current DPR before computing click coordinates.
- `clickxy` accepts floating-point CSS pixel values.
- Scroll the page with `eval` before taking a screenshot if the target element is below the fold.
- Use `click <selector>` instead of `clickxy` when you have a stable CSS selector — it handles scrolling and coordinate math automatically.
