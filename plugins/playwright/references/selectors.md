# Playwright Selector Guide

Best practices for selecting elements in Playwright.

## Selector Priority (Most to Least Preferred)

1. **Role-based** - `get_by_role()` - Most stable, accessibility-aware
2. **Label/Text** - `get_by_label()`, `get_by_text()` - User-visible
3. **Test ID** - `get_by_test_id()` - Explicitly for testing
4. **CSS/XPath** - `locator()` - Fallback only

## Role-Based Selectors (Preferred)

```python
# Buttons
page.get_by_role("button", name="Submit")
page.get_by_role("button", name="Submit", exact=True)  # Exact match
page.get_by_role("button", name=/submit/i)             # Regex

# Links
page.get_by_role("link", name="Sign up")
page.get_by_role("link", name="Home")

# Form elements
page.get_by_role("textbox", name="Email")
page.get_by_role("checkbox", name="Accept terms")
page.get_by_role("radio", name="Option A")
page.get_by_role("combobox", name="Country")           # Select dropdown
page.get_by_role("spinbutton", name="Quantity")        # Number input
page.get_by_role("slider", name="Volume")

# Structure
page.get_by_role("heading", name="Welcome", level=1)   # h1
page.get_by_role("heading", level=2)                   # Any h2
page.get_by_role("list")
page.get_by_role("listitem")
page.get_by_role("navigation")
page.get_by_role("main")
page.get_by_role("article")

# Tables
page.get_by_role("table")
page.get_by_role("row")
page.get_by_role("cell", name="Price")
page.get_by_role("columnheader", name="Name")

# Dialogs
page.get_by_role("dialog")
page.get_by_role("alertdialog")

# Media
page.get_by_role("img", name="Logo")
```

## Common ARIA Roles Reference

| Role | HTML Examples |
|------|--------------|
| `button` | `<button>`, `<input type="button">` |
| `link` | `<a href>` |
| `textbox` | `<input type="text">`, `<textarea>` |
| `checkbox` | `<input type="checkbox">` |
| `radio` | `<input type="radio">` |
| `combobox` | `<select>` |
| `listbox` | `<select>`, `<ul role="listbox">` |
| `option` | `<option>` |
| `heading` | `<h1>` - `<h6>` |
| `list` | `<ul>`, `<ol>` |
| `listitem` | `<li>` |
| `table` | `<table>` |
| `row` | `<tr>` |
| `cell` | `<td>` |
| `navigation` | `<nav>` |
| `main` | `<main>` |
| `article` | `<article>` |
| `dialog` | `<dialog>` |
| `img` | `<img>` |

## Text-Based Selectors

```python
# By visible label (for form elements)
page.get_by_label("Email address")
page.get_by_label("Password")
page.get_by_label(/email/i)                # Regex

# By placeholder
page.get_by_placeholder("Enter your email")
page.get_by_placeholder("Search...")

# By visible text
page.get_by_text("Click here")
page.get_by_text("Click here", exact=True)  # Exact match
page.get_by_text(/click/i)                  # Regex, case insensitive

# By alt text (images)
page.get_by_alt_text("Company Logo")
page.get_by_alt_text("User avatar")

# By title attribute
page.get_by_title("Close dialog")
page.get_by_title("Settings")
```

## Test ID Selectors

```python
# Using data-testid attribute (configurable)
page.get_by_test_id("submit-button")
page.get_by_test_id("user-email-input")
page.get_by_test_id("modal-close")

# HTML: <button data-testid="submit-button">Submit</button>
```

Configure custom test ID attribute:

```python
# In browser context
context = browser.new_context()
context.set_default_test_id_attribute("data-test")

# Now matches data-test instead of data-testid
page.get_by_test_id("my-element")
# Matches: <div data-test="my-element">
```

## Combining Locators

### OR - Match Either

```python
# Click whichever appears first
new_button = page.get_by_role("button", name="New")
create_button = page.get_by_role("button", name="Create")
new_button.or_(create_button).click()

# With first() for reliability
new_button.or_(create_button).first.click()
```

### AND - Match Both Conditions

```python
# Button that also has specific title
page.get_by_role("button").and_(
    page.get_by_title("Subscribe")
).click()

# Link with specific class (rare use case)
page.get_by_role("link").and_(
    page.locator(".external")
).click()
```

### Filter - Narrow Down Results

```python
# Table rows containing text
page.locator("tr").filter(has_text="Active").click()
page.locator("tr").filter(has_text=/active/i).click()

# List items containing a button
page.locator("li").filter(
    has=page.get_by_role("button", name="Edit")
).click()

# Combine filters
page.locator("tr").filter(has_text="Active").filter(
    has=page.get_by_role("button", name="Delete")
).first.click()

# NOT filter (exclude)
page.locator("li").filter(has_not_text="Archived").all()
page.locator("div").filter(
    has_not=page.get_by_role("button")
).all()
```

## CSS Selectors (Fallback)

```python
# Basic CSS
page.locator("button")
page.locator(".btn-primary")
page.locator("#submit")
page.locator("[type='submit']")

# Attribute selectors
page.locator("[data-value='123']")
page.locator("[href*='login']")            # Contains
page.locator("[href^='https']")            # Starts with
page.locator("[href$='.pdf']")             # Ends with

# Combinators
page.locator("form button")                # Descendant
page.locator("form > button")              # Direct child
page.locator("input + label")              # Adjacent sibling
page.locator("input ~ button")             # General sibling

# Pseudo-classes
page.locator("li:first-child")
page.locator("li:last-child")
page.locator("li:nth-child(3)")
page.locator("button:not(.disabled)")
page.locator("input:enabled")
page.locator("option:checked")
```

## XPath Selectors (Last Resort)

```python
# XPath with prefix
page.locator("xpath=//button[@type='submit']")
page.locator("xpath=//div[contains(@class, 'modal')]")
page.locator("xpath=//a[text()='Click me']")
page.locator("xpath=//input[@name='email']/following-sibling::button")
```

## Chaining Locators

```python
# Find within
modal = page.locator(".modal")
modal.get_by_role("button", name="Close").click()

# Multiple levels
page.locator("form").locator("fieldset").get_by_label("Email").fill("test@example.com")

# Frame locator
frame = page.frame_locator("#iframe")
frame.get_by_role("button", name="Submit").click()
```

## Selecting Multiple Elements

```python
# Count elements
count = page.locator("li").count()

# Get all elements
items = page.locator("li").all()
for item in items:
    print(item.text_content())

# Get specific by index
page.locator("li").first.click()
page.locator("li").last.click()
page.locator("li").nth(2).click()          # 0-indexed

# Get all text contents
texts = page.locator("li").all_text_contents()
```

## Best Practices

### DO

```python
# Prefer semantic, user-facing locators
page.get_by_role("button", name="Submit")
page.get_by_label("Email")
page.get_by_text("Welcome back")
page.get_by_test_id("checkout-button")
```

### DON'T

```python
# Avoid fragile selectors
page.locator("#root > div > div:nth-child(3) > button")  # Brittle
page.locator(".sc-hKgILt")                               # Generated class
page.locator("[class*='Button__StyledButton']")          # CSS-in-JS
page.locator("xpath=//div[3]/span[2]/button")            # Position-based
```

### Debugging Selectors

```python
# Check if selector matches
if page.locator("button").count() > 0:
    print("Found buttons")

# Highlight element (headed mode)
locator = page.get_by_role("button", name="Submit")
locator.highlight()

# Get selector playground
page.pause()  # Opens Playwright Inspector
```

## Common Selector Patterns

### Login form

```python
page.get_by_label("Email").fill("user@example.com")
page.get_by_label("Password").fill("secret")
page.get_by_role("button", name="Sign in").click()
```

### Search

```python
page.get_by_placeholder("Search...").fill("query")
page.get_by_role("button", name="Search").click()
# or
page.get_by_placeholder("Search...").press("Enter")
```

### Table row actions

```python
# Click Edit button in row containing "John"
page.locator("tr").filter(has_text="John").get_by_role("button", name="Edit").click()
```

### Modal dialog

```python
dialog = page.get_by_role("dialog")
dialog.get_by_role("button", name="Confirm").click()
```

### Navigation menu

```python
page.get_by_role("navigation").get_by_role("link", name="Settings").click()
```
