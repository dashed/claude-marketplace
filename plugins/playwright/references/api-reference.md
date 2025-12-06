# Playwright Python API Reference

Quick reference for common Playwright operations. For complete documentation, see [Playwright Python docs](https://playwright.dev/python/docs/api/class-playwright).

## Browser Launch

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Launch browsers
    browser = p.chromium.launch()       # Default: headless=True
    browser = p.firefox.launch()
    browser = p.webkit.launch()

    # Launch options
    browser = p.chromium.launch(
        headless=False,                  # Show browser UI
        slow_mo=100,                     # Slow down actions by 100ms
        args=["--disable-dev-shm-usage"],  # Chrome flags
        channel="chrome",                # Use installed Chrome
    )
```

## Browser Context

```python
# Create context with options
context = browser.new_context(
    viewport={"width": 1280, "height": 720},
    user_agent="Custom UA",
    locale="en-US",
    timezone_id="America/New_York",
    geolocation={"latitude": 40.7128, "longitude": -74.0060},
    permissions=["geolocation"],
    color_scheme="dark",                # or "light", "no-preference"
    device_scale_factor=2,              # Retina
    is_mobile=True,
    has_touch=True,
)

# Use device emulation
iphone = p.devices["iPhone 13"]
context = browser.new_context(**iphone)

# Reuse authentication state
context = browser.new_context(storage_state="auth.json")
```

## Page Navigation

```python
page = context.new_page()

# Navigation
page.goto("https://example.com")
page.goto(url, wait_until="domcontentloaded")  # or "load", "networkidle"
page.go_back()
page.go_forward()
page.reload()

# Wait for state
page.wait_for_load_state("networkidle")
page.wait_for_url("**/login")

# Timeouts
page.set_default_timeout(30_000)           # All operations
page.set_default_navigation_timeout(60_000)  # Navigation only
```

## Modern Locator API (Preferred)

```python
# Semantic locators - ALWAYS prefer these
page.get_by_role("button", name="Submit")
page.get_by_role("link", name="Sign up")
page.get_by_role("textbox", name="Email")
page.get_by_role("checkbox", name="Accept terms")

page.get_by_label("Email")
page.get_by_placeholder("Enter email")
page.get_by_text("Welcome")
page.get_by_text("Welcome", exact=True)    # Exact match
page.get_by_alt_text("Profile picture")
page.get_by_title("Settings")
page.get_by_test_id("submit-btn")          # data-testid attribute

# Locator combinators
btn = page.get_by_role("button", name="New")
dialog = page.get_by_text("Confirm")
btn.or_(dialog).first.click()              # Match either

page.get_by_role("button").and_(
    page.get_by_title("Subscribe")
).click()                                  # Match both

# Filtering
page.locator("tr").filter(has_text="Active").first.click()
page.locator("li").filter(
    has=page.get_by_role("button", name="Edit")
).click()
```

## CSS/XPath Locators (Fallback)

```python
# CSS selectors
page.locator("button.primary")
page.locator("#submit")
page.locator("[data-testid='submit']")
page.locator("form >> button")             # Chaining

# XPath
page.locator("xpath=//button[@type='submit']")

# Text matching
page.locator("text=Click me")
page.locator("text=/click/i")              # Regex, case insensitive
```

## Actions

```python
# Click
locator.click()
locator.click(button="right")              # Right-click
locator.click(click_count=2)               # Double-click
locator.click(modifiers=["Shift"])
locator.click(force=True)                  # Skip actionability checks
locator.click(position={"x": 10, "y": 10})

# Hover
locator.hover()

# Input
locator.fill("value")                      # Clear and type
locator.type("value")                      # Type char by char
locator.press("Enter")
locator.press("Control+a")
locator.clear()

# Checkboxes/Radio
locator.check()
locator.uncheck()
locator.set_checked(True)

# Select dropdown
locator.select_option("value")
locator.select_option(label="Option text")
locator.select_option(index=2)

# File upload
locator.set_input_files("file.pdf")
locator.set_input_files(["file1.pdf", "file2.pdf"])

# Drag and drop
locator.drag_to(target_locator)

# Focus/blur
locator.focus()
locator.blur()

# Scroll
locator.scroll_into_view_if_needed()
page.mouse.wheel(0, 500)                   # Scroll down
```

## Waiting

```python
# Wait for element
locator.wait_for()                         # visible by default
locator.wait_for(state="visible")
locator.wait_for(state="hidden")
locator.wait_for(state="attached")
locator.wait_for(state="detached")
locator.wait_for(timeout=5000)

# Wait for conditions
page.wait_for_selector("selector")
page.wait_for_url("**/success")
page.wait_for_function("() => window.ready")
page.wait_for_timeout(1000)                # Avoid if possible

# Wait for network
with page.expect_response("**/api/data") as response_info:
    page.click("button")
response = response_info.value
```

## Extracting Content

```python
# Text
locator.text_content()                     # Raw text
locator.inner_text()                       # Visible text
locator.inner_html()                       # Inner HTML
locator.all_text_contents()                # All matches

# Attributes
locator.get_attribute("href")
locator.get_attribute("value")

# Input values
locator.input_value()

# Count and existence
locator.count()
locator.is_visible()
locator.is_enabled()
locator.is_checked()

# Multiple elements
for item in locator.all():
    print(item.text_content())
```

## Screenshots

```python
# Page screenshot
page.screenshot(path="/tmp/screenshot.png")
page.screenshot(path="/tmp/full.png", full_page=True)
page.screenshot(type="jpeg", quality=80)

# Element screenshot
locator.screenshot(path="/tmp/element.png")

# Return bytes (no file)
bytes_data = page.screenshot()
```

## JavaScript Execution

```python
# Evaluate expression
title = page.evaluate("document.title")
count = page.evaluate("document.querySelectorAll('a').length")

# Evaluate with arguments
result = page.evaluate("([a, b]) => a + b", [1, 2])

# Evaluate function
result = page.evaluate("""
    () => {
        return window.localStorage.getItem('key');
    }
""")

# Evaluate on element
href = locator.evaluate("el => el.href")
```

## Network

```python
# Intercept requests
def handle_route(route):
    if "ads" in route.request.url:
        route.abort()
    else:
        route.continue_()

page.route("**/*", handle_route)

# Mock API response
page.route("**/api/user", lambda route: route.fulfill(
    status=200,
    content_type="application/json",
    body='{"name": "Test User"}'
))

# Wait for response
with page.expect_response("**/api/data") as response_info:
    page.click("button")
data = response_info.value.json()
```

## Frames and Popups

```python
# Frames
frame = page.frame(name="frame-name")
frame = page.frame_locator("#iframe").locator("button")
frame.click()

# Popups
with page.expect_popup() as popup_info:
    page.click("a[target='_blank']")
popup = popup_info.value
popup.wait_for_load_state()
print(popup.title())
```

## Tracing

```python
# Start tracing
context.tracing.start(screenshots=True, snapshots=True, sources=True)

# Your automation...

# Stop and save
context.tracing.stop(path="trace.zip")

# View trace
# uv run --with playwright playwright show-trace trace.zip
```

## Clock API (Time Mocking)

```python
import datetime

# Install fake timers
page.clock.install(time=datetime.datetime(2024, 12, 10, 8, 0, 0))
page.goto("https://example.com")

# Fast forward
page.clock.fast_forward(1000)              # 1 second
page.clock.fast_forward("30:00")           # 30 minutes

# Pause at specific time
page.clock.pause_at(datetime.datetime(2024, 12, 10, 10, 0, 0))

# Resume normal flow
page.clock.resume()
```

## ARIA Snapshots

```python
from playwright.sync_api import expect

# Get ARIA snapshot (YAML format)
snapshot = page.get_by_role("navigation").aria_snapshot()
print(snapshot)

# Assert ARIA structure
expect(page.locator("nav")).to_match_aria_snapshot('''
- navigation:
  - link "Home"
  - link "About"
  - link "Contact"
''')
```

## Session Storage

```python
# Save auth state after login
context.storage_state(path="auth.json")

# Reuse in new context
context = browser.new_context(storage_state="auth.json")
```

## Common Patterns

### Login with session reuse

```python
# First time: login and save state
page.goto("https://example.com/login")
page.get_by_label("Email").fill("user@example.com")
page.get_by_label("Password").fill("password")
page.get_by_role("button", name="Sign in").click()
page.wait_for_url("**/dashboard")
context.storage_state(path="auth.json")

# Subsequent runs: reuse state
context = browser.new_context(storage_state="auth.json")
page = context.new_page()
page.goto("https://example.com/dashboard")  # Already logged in
```

### Handle dynamic content

```python
# Wait for network idle
page.goto(url, wait_until="networkidle")

# Wait for specific element
page.get_by_text("Loaded").wait_for()

# Wait for element count
page.locator(".item").nth(9).wait_for()    # Wait for 10 items
```

### Retry on failure

```python
from playwright.sync_api import expect

# Built-in retry with expect
expect(locator).to_be_visible(timeout=10_000)
expect(locator).to_have_text("Success")
expect(locator).to_have_count(5)
```
