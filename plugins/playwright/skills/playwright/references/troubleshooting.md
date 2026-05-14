# Playwright Troubleshooting Guide

Common issues and solutions when using Playwright.

## Browser Installation Issues

> **Claude: Do not run browser installation commands directly.** Suggest these commands to the user and let them run manually.

### "Executable doesn't exist" / "Browser not found"

**Cause**: Playwright browser binaries not installed.

**Solution** (suggest to user, do not run directly):
```bash
# Install Chromium (recommended, ~200MB)
uv run --with playwright playwright install chromium

# Install all browsers
uv run --with playwright playwright install

# Install with system dependencies (Linux)
uv run --with playwright playwright install --with-deps chromium
```

### "Missing system dependencies" (Linux)

**Cause**: Required system libraries not installed.

**Solution**:
```bash
# Install dependencies automatically
uv run --with playwright playwright install-deps chromium

# Or manually on Ubuntu/Debian
sudo apt-get install libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2
```

### Browser location not detected

**Check installed browsers**:
```bash
uv run /path/to/plugins/playwright/scripts/check_setup.py
```

**Browser cache locations**:
- macOS: `~/Library/Caches/ms-playwright/`
- Linux: `~/.cache/ms-playwright/`
- Windows: `%USERPROFILE%\AppData\Local\ms-playwright\`

**Custom browser path**:
```python
browser = p.chromium.launch(
    executable_path="/path/to/chromium"
)
```

## Timeout Issues

### "Timeout waiting for element"

**Causes**:
- Element doesn't exist
- Element is hidden or not rendered
- Wrong selector
- Page still loading

**Solutions**:

```python
# 1. Increase timeout
page.set_default_timeout(60_000)
locator.click(timeout=30_000)

# 2. Wait for network idle
page.goto(url, wait_until="networkidle")

# 3. Wait for element explicitly
page.get_by_role("button", name="Submit").wait_for(state="visible")

# 4. Check element exists
if page.get_by_role("button", name="Submit").count() > 0:
    page.get_by_role("button", name="Submit").click()
else:
    print("Button not found")
```

### "Navigation timeout"

**Causes**:
- Slow page load
- Page waiting for external resources
- Infinite redirects

**Solutions**:

```python
# 1. Increase navigation timeout
page.set_default_navigation_timeout(120_000)

# 2. Use different wait strategy
page.goto(url, wait_until="domcontentloaded")  # Faster than "load"

# 3. Don't wait for all network activity
page.goto(url, wait_until="commit")
```

## Element Interaction Issues

### "Element is not visible"

**Solutions**:

```python
# 1. Scroll into view
element = page.get_by_role("button", name="Submit")
element.scroll_into_view_if_needed()
element.click()

# 2. Force click (skip visibility check)
element.click(force=True)

# 3. Wait for visibility
element.wait_for(state="visible")
element.click()
```

### "Element is not enabled"

**Cause**: Button or input is disabled.

**Solutions**:

```python
# 1. Wait for element to be enabled
page.get_by_role("button", name="Submit").wait_for(state="attached")
page.wait_for_function("document.querySelector('button').disabled === false")
page.get_by_role("button", name="Submit").click()

# 2. Check element state
btn = page.get_by_role("button", name="Submit")
if btn.is_enabled():
    btn.click()
```

### "Element is detached from DOM"

**Cause**: Page updated and element was removed/replaced.

**Solution**:

```python
# Re-query the element
page.get_by_role("button", name="Submit").click()  # Always fresh query
```

### "Multiple elements match selector"

**Solutions**:

```python
# 1. Use more specific selector
page.get_by_role("button", name="Submit", exact=True)

# 2. Use first/last/nth
page.locator("button").first.click()
page.locator("button").nth(2).click()

# 3. Filter results
page.locator("button").filter(has_text="Submit").click()
```

## Frame and Popup Issues

### "Element not found" (in iframe)

**Solution**:

```python
# Locate frame first
frame = page.frame_locator("#iframe")
frame.get_by_role("button", name="Submit").click()

# Or by name
frame = page.frame(name="content-frame")
frame.locator("button").click()
```

### Popup window not captured

**Solution**:

```python
# Wait for popup before clicking
with page.expect_popup() as popup_info:
    page.get_by_role("link", name="Open").click()

popup = popup_info.value
popup.wait_for_load_state()
print(popup.title())
```

## Headless Mode Issues

### Page renders differently in headless mode

**Causes**:
- Different viewport
- Missing fonts
- GPU rendering differences

**Solutions**:

```python
# 1. Set explicit viewport
context = browser.new_context(
    viewport={"width": 1920, "height": 1080}
)

# 2. Debug in headed mode first
browser = p.chromium.launch(headless=False)

# 3. Use device emulation for consistency
iphone = p.devices["iPhone 13"]
context = browser.new_context(**iphone)
```

### "Page crash" in headless

**Cause**: Often memory or resource issues.

**Solution** (especially in Docker):

```python
browser = p.chromium.launch(
    headless=True,
    args=[
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--no-sandbox",
        "--single-process",
    ]
)
```

## Network Issues

### SSL certificate errors

**Solution**:

```python
context = browser.new_context(
    ignore_https_errors=True
)
```

### Requests blocked by CORS

**Cause**: Browser enforces CORS, unlike requests library.

**Solution**: This is expected browser behavior. To bypass:

```python
# Intercept and modify response headers
page.route("**/*", lambda route: route.continue_(
    headers={**route.request.headers, "Access-Control-Allow-Origin": "*"}
))
```

### Page blocked by bot detection

**Solutions**:

```python
# 1. Use stealth settings
context = browser.new_context(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
    viewport={"width": 1920, "height": 1080},
    locale="en-US",
)

# 2. Use slow_mo to appear more human
browser = p.chromium.launch(slow_mo=100)

# 3. Add random delays
import random
import time
time.sleep(random.uniform(0.5, 1.5))
```

## File Downloads

### Download not triggered

**Solution**:

```python
# Wait for download
with page.expect_download() as download_info:
    page.get_by_role("link", name="Download").click()

download = download_info.value
download.save_as("/tmp/file.pdf")
print(f"Downloaded: {download.path()}")
```

### Downloads blocked

**Solution**:

```python
context = browser.new_context(
    accept_downloads=True
)
```

## Performance Issues

### Script runs slowly

**Solutions**:

```python
# 1. Use headless mode
browser = p.chromium.launch(headless=True)

# 2. Disable images/CSS for faster loads
context = browser.new_context()
await page.route("**/*.{png,jpg,jpeg,gif,webp,css}", lambda route: route.abort())

# 3. Use networkidle only when necessary
page.goto(url, wait_until="domcontentloaded")  # Faster

# 4. Close browser when done
browser.close()
```

### Memory leaks

**Solution**:

```python
# Always use context manager
with sync_playwright() as p:
    browser = p.chromium.launch()
    # ... automation ...
    browser.close()  # Explicit close

# Or try/finally
try:
    browser = p.chromium.launch()
    # ...
finally:
    browser.close()
```

## Debugging Techniques

### Use Playwright Inspector

```python
page.pause()  # Opens inspector
```

### Enable verbose logging

```bash
DEBUG=pw:api uv run /tmp/script.py
```

### Take screenshots on failure

```python
try:
    # automation code
except Exception as e:
    page.screenshot(path="/tmp/error.png")
    raise
```

### Record trace for debugging

```python
context.tracing.start(screenshots=True, snapshots=True, sources=True)
# ... automation ...
context.tracing.stop(path="/tmp/trace.zip")
```

View trace:
```bash
uv run --with playwright playwright show-trace /tmp/trace.zip
```

### Console log from page

```python
page.on("console", lambda msg: print(f"Console: {msg.text}"))
page.on("pageerror", lambda err: print(f"Page error: {err}"))
```

## Docker/CI Specific

### Running in Docker

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.56.0

WORKDIR /app
COPY script.py .

CMD ["python", "script.py"]
```

### GitHub Actions

```yaml
- name: Install Playwright
  run: |
    pip install playwright==1.56.0
    playwright install chromium --with-deps
```

### Environment variables for CI

```bash
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
export XDG_CACHE_HOME=/tmp/.cache
```
