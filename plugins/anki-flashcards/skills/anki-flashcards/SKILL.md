---
name: anki-flashcards
description: Create and manage Anki flashcards via the AnkiConnect API. Use when the user wants to create flashcards, add cards to Anki, manage Anki decks, review Anki statistics, or interact with Anki in any way. Requires Anki desktop app running with AnkiConnect add-on installed.
---

# Anki Flashcards

Create, search, update, and manage Anki flashcards programmatically via the AnkiConnect HTTP API on `localhost:8765`. All operations use `curl` with JSON payloads — no SDK or library required.

## Prerequisites

Before using this skill, the user must have the following set up. **Do not attempt to install these — guide the user through the steps.**

### 1. Anki Desktop App

Anki must be installed and running. Download from https://apps.ankiweb.net/

### 2. AnkiConnect Add-on

Install the AnkiConnect add-on inside Anki:

1. Open Anki
2. Go to **Tools → Add-ons → Get Add-ons...**
3. Enter code: `2055492159`
4. Click **OK** and restart Anki

### 3. Platform-Specific Setup

**macOS** — Disable App Nap to prevent Anki from being suspended in the background:

```bash
defaults write net.ankiweb.dtop NSAppSleepDisabled -bool true
defaults write net.ichi2.anki NSAppSleepDisabled -bool true
defaults write org.qt-project.Qt.QtWebEngineCore NSAppSleepDisabled -bool true
```

**Windows** — Allow Anki through Windows Firewall if connections to `localhost:8765` are blocked.

### 4. Verify Connectivity

```bash
curl -s localhost:8765 -X POST -d '{"action": "requestPermission", "version": 6}'
```

Expected response includes `"permission": "granted"`. If the connection is refused, Anki is not running or AnkiConnect is not installed.

## Connectivity Check

Always verify AnkiConnect is reachable before performing any operations:

```bash
curl -s localhost:8765 -X POST -d '{"action": "requestPermission", "version": 6}'
```

If this fails, tell the user to:
1. Ensure Anki is open
2. Confirm AnkiConnect is installed (Tools → Add-ons should list AnkiConnect)
3. Restart Anki after installing the add-on

## Core Workflows

All requests use HTTP POST to `localhost:8765` with this JSON structure:

```json
{"action": "actionName", "version": 6, "params": {...}}
```

Responses return: `{"result": <value>, "error": <null or string>}`

### Creating Flashcards

**Single card (Basic model):**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addNote",
  "version": 6,
  "params": {
    "note": {
      "deckName": "Spanish Vocabulary",
      "modelName": "Basic",
      "fields": {"Front": "casa", "Back": "house"},
      "tags": ["spanish", "beginner"]
    }
  }
}'
```

**Batch create multiple cards:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addNotes",
  "version": 6,
  "params": {
    "notes": [
      {
        "deckName": "Biology",
        "modelName": "Basic",
        "fields": {"Front": "What is mitosis?", "Back": "Cell division producing two identical daughter cells"},
        "tags": ["biology", "cell-division"]
      },
      {
        "deckName": "Biology",
        "modelName": "Basic",
        "fields": {"Front": "What is meiosis?", "Back": "Cell division producing four genetically diverse gametes"},
        "tags": ["biology", "cell-division"]
      }
    ]
  }
}'
```

**Cloze deletion card:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addNote",
  "version": 6,
  "params": {
    "note": {
      "deckName": "Programming",
      "modelName": "Cloze",
      "fields": {"Text": "In Python, {{c1::list comprehensions}} create lists from {{c2::iterables}} using a concise syntax."},
      "tags": ["python", "syntax"]
    }
  }
}'
```

**Card with media (image or audio):**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addNote",
  "version": 6,
  "params": {
    "note": {
      "deckName": "Geography",
      "modelName": "Basic",
      "fields": {"Front": "Identify this country", "Back": "Japan"},
      "tags": ["geography"],
      "picture": [{
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Japan.svg/320px-Flag_of_Japan.svg.png",
        "filename": "japan_flag.png",
        "fields": ["Front"]
      }]
    }
  }
}'
```

### Finding Cards

**Search by deck and tag:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "findNotes",
  "version": 6,
  "params": {"query": "deck:Spanish tag:beginner"}
}'
```

**Get full card details from note IDs:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "notesInfo",
  "version": 6,
  "params": {"notes": [1234567890, 1234567891]}
}'
```

**Common search queries:**
- `deck:DeckName` — all notes in a deck
- `tag:tagname` — all notes with a tag
- `is:due` — cards due for review
- `is:new` — cards never reviewed
- `added:7` — cards added in the last 7 days
- `"front:casa"` — search a specific field
- Combine with spaces (AND): `deck:Spanish tag:beginner is:due`
- Negate with `-`: `deck:Spanish -tag:advanced`

### Updating Cards

**Update note fields:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "updateNote",
  "version": 6,
  "params": {
    "note": {
      "id": 1234567890,
      "fields": {"Front": "casa (noun)", "Back": "house, home"},
      "tags": ["spanish", "beginner", "nouns"]
    }
  }
}'
```

**Add tags to notes:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addTags",
  "version": 6,
  "params": {"notes": [1234567890, 1234567891], "tags": "reviewed important"}
}'
```

**Remove tags from notes:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "removeTags",
  "version": 6,
  "params": {"notes": [1234567890], "tags": "beginner"}
}'
```

### Managing Decks

**Create a deck (supports `::` hierarchy):**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "createDeck",
  "version": 6,
  "params": {"deck": "Languages::Spanish::Vocabulary"}
}'
```

**List all decks:**

```bash
curl -s localhost:8765 -X POST -d '{"action": "deckNames", "version": 6}'
```

**Get deck statistics:**

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "getDeckStats",
  "version": 6,
  "params": {"decks": ["Spanish Vocabulary"]}
}'
```

Returns new/learning/review counts per deck.

### Batch Operations

Use the `multi` action to execute multiple operations in a single request for efficiency:

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "multi",
  "version": 6,
  "params": {
    "actions": [
      {"action": "createDeck", "params": {"deck": "Chemistry"}},
      {"action": "addNote", "params": {
        "note": {
          "deckName": "Chemistry",
          "modelName": "Basic",
          "fields": {"Front": "What is the atomic number of Carbon?", "Back": "6"},
          "tags": ["chemistry", "elements"]
        }
      }},
      {"action": "addNote", "params": {
        "note": {
          "deckName": "Chemistry",
          "modelName": "Basic",
          "fields": {"Front": "What is Avogadro'\''s number?", "Back": "6.022 × 10²³"},
          "tags": ["chemistry", "constants"]
        }
      }}
    ]
  }
}'
```

Use `multi` when creating a deck and populating it with cards, or when performing several independent operations.

### Custom Note Types

Create a custom model when Basic and Cloze are insufficient:

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "createModel",
  "version": 6,
  "params": {
    "modelName": "Vocabulary Card",
    "inOrderFields": ["Word", "Definition", "Example", "PartOfSpeech"],
    "css": ".card { font-family: arial; font-size: 20px; text-align: center; }",
    "cardTemplates": [
      {
        "Name": "Word → Definition",
        "Front": "<div class=\"word\">{{Word}}</div><div class=\"pos\">{{PartOfSpeech}}</div>",
        "Back": "{{FrontSide}}<hr id=\"answer\"><div class=\"def\">{{Definition}}</div><div class=\"example\"><i>{{Example}}</i></div>"
      }
    ]
  }
}'
```

## Quick Reference

| Action | Description | Key Params |
|--------|-------------|------------|
| `addNote` | Create a single card | `note: {deckName, modelName, fields, tags}` |
| `addNotes` | Create multiple cards | `notes: [{...}, ...]` |
| `findNotes` | Search for notes | `query` (Anki search syntax) |
| `notesInfo` | Get note details | `notes: [id, ...]` |
| `updateNote` | Update fields/tags | `note: {id, fields, tags}` |
| `addTags` | Add tags to notes | `notes: [id, ...], tags: "tag1 tag2"` |
| `removeTags` | Remove tags | `notes: [id, ...], tags: "tag1"` |
| `createDeck` | Create a deck | `deck: "Name"` (use `::` for hierarchy) |
| `deckNames` | List all decks | (none) |
| `getDeckStats` | Deck review stats | `decks: ["Name"]` |
| `deleteDecks` | Delete decks | `decks: ["Name"], cardsToo: true` |
| `multi` | Batch operations | `actions: [{action, params}, ...]` |
| `createModel` | Custom note type | `modelName, inOrderFields, cardTemplates` |
| `storeMediaFile` | Upload media | `filename, data/url/path` |
| `sync` | Trigger AnkiWeb sync | (none) |

## Flashcard Design Tips

- **One concept per card** — atomic cards are easier to review and schedule
- **Use cloze deletions** for definitions, formulas, and fill-in-the-blank recall
- **Add context with tags** — use hierarchical tags like `spanish::verbs::irregular` for organization
- **Include examples** — concrete examples improve retention over abstract definitions
- **Avoid "yes/no" cards** — rephrase to require recall of the actual answer

For comprehensive flashcard design principles, see [references/card-design.md](references/card-design.md).

## Advanced Usage

For complete API documentation covering all 100+ AnkiConnect actions, see [references/api-reference.md](references/api-reference.md).

For flashcard design principles and evidence-based learning strategies, see [references/card-design.md](references/card-design.md).
