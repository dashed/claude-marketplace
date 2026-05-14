# AnkiConnect API Reference

Complete reference for all AnkiConnect actions. All requests use HTTP POST to `localhost:8765`.

## Protocol

**Request format:**

```json
{"action": "actionName", "version": 6, "params": {...}}
```

**Response format:**

```json
{"result": <value>, "error": <null or error string>}
```

Every request must include `"version": 6`. Omitting it or using an older version may produce unexpected behavior.

---

## Table of Contents

- [Note Actions](#note-actions)
- [Card Actions](#card-actions)
- [Deck Actions](#deck-actions)
- [Model Actions](#model-actions)
- [Media Actions](#media-actions)
- [Statistic Actions](#statistic-actions)
- [Graphical Actions](#graphical-actions)
- [Miscellaneous Actions](#miscellaneous-actions)
- [Search Query Syntax](#search-query-syntax)

---

## Note Actions

Notes are the primary data objects in Anki. Each note produces one or more cards based on its model (note type).

### addNote

Create a single note. Returns the note ID on success, `null` if a duplicate.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addNote",
  "version": 6,
  "params": {
    "note": {
      "deckName": "Spanish Vocabulary",
      "modelName": "Basic",
      "fields": {"Front": "casa", "Back": "house, home"},
      "options": {
        "allowDuplicate": false,
        "duplicateScope": "deck",
        "duplicateScopeOptions": {
          "deckName": "Spanish Vocabulary",
          "checkChildren": false,
          "checkAllModels": false
        }
      },
      "tags": ["spanish", "nouns"],
      "audio": [{
        "url": "https://example.com/casa.mp3",
        "filename": "casa.mp3",
        "fields": ["Front"]
      }],
      "picture": [{
        "url": "https://example.com/house.jpg",
        "filename": "house.jpg",
        "fields": ["Back"]
      }]
    }
  }
}'
```

**Params:**
- `note.deckName` — target deck (created if missing)
- `note.modelName` — note type (`Basic`, `Cloze`, or custom)
- `note.fields` — object mapping field names to values (HTML allowed)
- `note.tags` — array of tag strings
- `note.options.allowDuplicate` — allow duplicate notes (default: `false`)
- `note.options.duplicateScope` — `"deck"` to check within deck only
- `note.audio` / `note.video` / `note.picture` — media attachments with `url`/`data`/`path`, `filename`, and `fields`

### addNotes

Create multiple notes in a single request. Returns array of note IDs (null for failures).

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addNotes",
  "version": 6,
  "params": {
    "notes": [
      {
        "deckName": "Biology",
        "modelName": "Basic",
        "fields": {"Front": "What is DNA?", "Back": "Deoxyribonucleic acid — carries genetic instructions"},
        "tags": ["biology", "genetics"]
      },
      {
        "deckName": "Biology",
        "modelName": "Basic",
        "fields": {"Front": "What is RNA?", "Back": "Ribonucleic acid — translates genetic code into proteins"},
        "tags": ["biology", "genetics"]
      }
    ]
  }
}'
```

### canAddNotes

Check if notes can be added without actually adding them. Returns array of booleans.

**Params:** `notes` — same structure as `addNotes`

### canAddNotesWithErrorDetail

Like `canAddNotes` but returns error details for each note that cannot be added.

**Params:** `notes` — same structure as `addNotes`

### findNotes

Search for notes using Anki's query syntax. Returns array of note IDs.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "findNotes",
  "version": 6,
  "params": {"query": "deck:Spanish tag:beginner is:due"}
}'
```

**Params:** `query` — see [Search Query Syntax](#search-query-syntax)

### notesInfo

Get full details for notes by ID. Returns array of note objects with fields, tags, model, cards, and modification time.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "notesInfo",
  "version": 6,
  "params": {"notes": [1234567890]}
}'
```

**Returns:** Array of objects with `noteId`, `modelName`, `fields`, `tags`, `cards`, `mod`.

### notesModTime

Get modification timestamps for notes. Returns array of `{id, mod}` objects.

**Params:** `notes` — array of note IDs

### updateNoteFields

Update only the fields of a note (legacy — prefer `updateNote`).

**Params:** `note: {id, fields}`

### updateNote

Update fields and/or tags of an existing note.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "updateNote",
  "version": 6,
  "params": {
    "note": {
      "id": 1234567890,
      "fields": {"Front": "casa (noun, feminine)", "Back": "house, home, household"},
      "tags": ["spanish", "nouns", "feminine"]
    }
  }
}'
```

**Params:** `note: {id, fields, tags}` — `fields` and `tags` are both optional

### updateNoteModel

Change the model (note type) of an existing note, remapping fields and templates.

**Params:** `note: {id, modelName, fields, tags}`

### updateNoteTags

Replace all tags on a note.

**Params:** `note: {id, tags}`

### getNoteTags

Get tags for a specific note.

**Params:** `note` — note ID (integer)

### addTags

Add tags to one or more notes.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "addTags",
  "version": 6,
  "params": {"notes": [1234567890, 1234567891], "tags": "reviewed important"}
}'
```

**Params:** `notes` — array of note IDs, `tags` — space-separated tag string

### removeTags

Remove tags from one or more notes.

**Params:** `notes` — array of note IDs, `tags` — space-separated tag string

### getTags

Get all tags in the collection. No params. Returns array of strings.

### clearUnusedTags

Remove tags not assigned to any notes. No params.

### replaceTags

Replace a tag on specific notes.

**Params:** `notes` — array of note IDs, `tag_to_replace`, `replace_with_tag`

### replaceTagsInAllNotes

Replace a tag across the entire collection.

**Params:** `tag_to_replace`, `replace_with_tag`

### deleteNotes

Delete notes by ID.

**Params:** `notes` — array of note IDs

### removeEmptyNotes

Remove notes that have no cards. No params.

---

## Card Actions

Cards are generated from notes. A note with multiple card templates produces multiple cards.

### findCards

Search for cards using Anki's query syntax. Returns array of card IDs.

**Params:** `query` — see [Search Query Syntax](#search-query-syntax)

### cardsInfo

Get full details for cards by ID. Returns array of card objects.

**Params:** `cards` — array of card IDs

### cardsToNotes

Convert card IDs to their parent note IDs. Returns array of note IDs.

**Params:** `cards` — array of card IDs

### cardsModTime

Get modification timestamps for cards. Returns array of `{cardId, mod}` objects.

**Params:** `cards` — array of card IDs

### getEaseFactors

Get ease factors for cards. Returns array of integers (e.g., 2500 = 250%).

**Params:** `cards` — array of card IDs

### setEaseFactors

Set ease factors for cards. Returns array of booleans indicating success.

**Params:** `cards` — array of card IDs, `easeFactors` — array of integers

### setSpecificValueOfCard

Set a specific property on a card (e.g., ease, queue, type, due, ivl, etc.).

**Params:** `card` — card ID, `keys` — array of property names, `newValues` — array of values

### suspend

Suspend cards (exclude from review). Returns `true`.

**Params:** `cards` — array of card IDs

### unsuspend

Unsuspend cards. Returns `true`.

**Params:** `cards` — array of card IDs

### suspended

Check if a card is suspended. Returns boolean.

**Params:** `card` — card ID

### areSuspended

Check if multiple cards are suspended. Returns array of booleans.

**Params:** `cards` — array of card IDs

### areDue

Check if cards are due for review. Returns array of booleans.

**Params:** `cards` — array of card IDs

### getIntervals

Get review intervals for cards. Returns array of intervals (in days).

**Params:** `cards` — array of card IDs, `complete` — boolean (if true, returns all intervals in review history)

### forgetCards

Reset cards to new state (removes review history scheduling).

**Params:** `cards` — array of card IDs

### relearnCards

Move cards to relearning queue.

**Params:** `cards` — array of card IDs

### answerCards

Programmatically answer cards. Each answer object specifies a card and an ease rating.

**Params:** `answers` — array of `{cardId, ease}` where ease is 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)

### setDueDate

Set the due date for cards.

**Params:** `cards` — array of card IDs, `days` — string (e.g., `"0"` for today, `"3"` for 3 days, `"2025-12-25"`)

---

## Deck Actions

### createDeck

Create a deck. Use `::` for hierarchical sub-decks (e.g., `"Languages::Spanish::Verbs"`). Returns deck ID.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "createDeck",
  "version": 6,
  "params": {"deck": "Languages::Spanish::Vocabulary"}
}'
```

### deckNames

List all deck names. No params. Returns array of strings.

### deckNamesAndIds

List all decks with their IDs. No params. Returns object mapping name to ID.

### getDecks

Get deck names for given card IDs.

**Params:** `cards` — array of card IDs

### changeDeck

Move cards to a different deck.

**Params:** `cards` — array of card IDs, `deck` — target deck name

### deleteDecks

Delete decks. **Must set `cardsToo: true`** or the call will fail.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "deleteDecks",
  "version": 6,
  "params": {"decks": ["Old Deck"], "cardsToo": true}
}'
```

### getDeckConfig

Get the configuration object for a deck.

**Params:** `deck` — deck name

### saveDeckConfig

Save a modified deck configuration.

**Params:** `config` — config object (as returned by `getDeckConfig`)

### setDeckConfigId

Assign a config group to decks.

**Params:** `decks` — array of deck names, `configId` — config group ID

### cloneDeckConfigId

Clone a config group. Returns new config ID.

**Params:** `cloneFrom` — source config ID, `name` — name for new group

### removeDeckConfigId

Delete a config group. Returns `true`. Cannot delete default config (ID 1).

**Params:** `configId` — config group ID

### getDeckStats

Get review statistics for decks.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "getDeckStats",
  "version": 6,
  "params": {"decks": ["Spanish Vocabulary", "Biology"]}
}'
```

**Returns:** Object mapping deck IDs to stats including `new_count`, `learn_count`, `review_count`, `total_in_deck`.

---

## Model Actions

Models (note types) define the fields and card templates for notes.

### modelNames

List all model names. No params. Returns array of strings.

### modelNamesAndIds

List all models with IDs. No params. Returns object mapping name to ID.

### findModelsById

Find models by ID.

**Params:** `modelIds` — array of model IDs

### findModelsByName

Find models by name.

**Params:** `modelNames` — array of model names

### modelFieldNames

Get field names for a model.

**Params:** `modelName` — model name. Returns array of strings.

### modelFieldDescriptions

Get field descriptions for a model.

**Params:** `modelName` — model name

### modelFieldFonts

Get font settings for model fields.

**Params:** `modelName` — model name

### modelFieldsOnTemplates

Get which fields are used on which card templates.

**Params:** `modelName` — model name

### createModel

Create a custom note type with fields, templates, and CSS.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "createModel",
  "version": 6,
  "params": {
    "modelName": "Language Card",
    "inOrderFields": ["Word", "Reading", "Definition", "Example", "Notes"],
    "css": ".card { font-family: arial; font-size: 20px; text-align: center; color: #333; }\n.word { font-size: 36px; font-weight: bold; }\n.reading { color: #666; font-style: italic; }\n.example { margin-top: 10px; font-size: 16px; }",
    "isCloze": false,
    "cardTemplates": [
      {
        "Name": "Recognition",
        "Front": "<div class=\"word\">{{Word}}</div><div class=\"reading\">{{Reading}}</div>",
        "Back": "{{FrontSide}}<hr id=\"answer\"><div>{{Definition}}</div><div class=\"example\">{{Example}}</div>"
      },
      {
        "Name": "Recall",
        "Front": "<div>{{Definition}}</div>",
        "Back": "{{FrontSide}}<hr id=\"answer\"><div class=\"word\">{{Word}}</div><div class=\"reading\">{{Reading}}</div><div class=\"example\">{{Example}}</div>"
      }
    ]
  }
}'
```

**Params:**
- `modelName` — unique name for the model
- `inOrderFields` — array of field names in order
- `css` — CSS styling for cards
- `isCloze` — `true` for cloze deletion models
- `cardTemplates` — array of `{Name, Front, Back}` objects using `{{FieldName}}` placeholders

### modelTemplates

Get card templates for a model.

**Params:** `modelName`

### modelStyling

Get CSS styling for a model.

**Params:** `modelName`

### updateModelTemplates

Update card templates for a model.

**Params:** `model: {name, templates: {TemplateName: {Front, Back}}}`

### updateModelStyling

Update CSS for a model.

**Params:** `model: {name, css}`

### findAndReplaceInModels

Find and replace text in model templates.

**Params:** `model: {modelName, findText, replaceText, front, back, css}`

### modelTemplateRename

Rename a card template.

**Params:** `modelName`, `oldTemplateName`, `newTemplateName`

### modelTemplateReposition

Reorder a card template.

**Params:** `modelName`, `templateName`, `index`

### modelTemplateAdd

Add a new card template to a model.

**Params:** `modelName`, `template: {Name, Front, Back}`

### modelTemplateRemove

Remove a card template from a model.

**Params:** `modelName`, `templateName`

### modelFieldRename

Rename a field.

**Params:** `modelName`, `oldFieldName`, `newFieldName`

### modelFieldReposition

Reorder a field.

**Params:** `modelName`, `fieldName`, `index`

### modelFieldAdd

Add a new field to a model.

**Params:** `modelName`, `fieldName`, `index` (optional)

### modelFieldRemove

Remove a field from a model.

**Params:** `modelName`, `fieldName`

### modelFieldSetFont

Set the editor font for a field.

**Params:** `modelName`, `fieldName`, `font`

### modelFieldSetFontSize

Set the editor font size for a field.

**Params:** `modelName`, `fieldName`, `fontSize`

### modelFieldSetDescription

Set description text for a field.

**Params:** `modelName`, `fieldName`, `description`

---

## Media Actions

### storeMediaFile

Store a media file in Anki's media folder. Supports three sources: base64 data, file path, or URL.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "storeMediaFile",
  "version": 6,
  "params": {
    "filename": "pronunciation.mp3",
    "url": "https://example.com/audio/word.mp3"
  }
}'
```

**Params (choose one source):**
- `filename` + `data` — base64-encoded file content
- `filename` + `path` — absolute path to a local file
- `filename` + `url` — URL to download from

Prefix filename with `_` (e.g., `_myfile.jpg`) to prevent Anki from deleting it during unused media cleanup.

### retrieveMediaFile

Get a media file as base64 string.

**Params:** `filename` — name of the file in Anki's media folder

### getMediaFilesNames

List media files matching a pattern.

**Params:** `pattern` — glob pattern (e.g., `"*.mp3"`, `"vocab_*"`)

### getMediaDirPath

Get the absolute path to Anki's media directory. No params.

### deleteMediaFile

Delete a media file.

**Params:** `filename` — name of the file to delete

---

## Statistic Actions

### getNumCardsReviewedToday

Get the number of cards reviewed today. No params. Returns integer.

### getNumCardsReviewedByDay

Get daily review counts. No params. Returns array of `[date, count]` pairs.

### getCollectionStatsHTML

Get collection statistics as HTML (same as Anki's Stats screen).

**Params:** `wholeCollection` — boolean (true for all decks, false for current deck)

### cardReviews

Get review history for a deck since a given timestamp.

**Params:** `deck` — deck name, `startID` — Unix timestamp in milliseconds

### getReviewsOfCards

Get review history for specific cards.

**Params:** `cards` — array of card IDs

### getLatestReviewID

Get the timestamp of the most recent review. No params. Returns integer (Unix ms).

### insertReviews

Insert review history entries (for migration/restore).

**Params:** `reviews` — array of review objects with `id`, `usn`, `ease`, `ivl`, `lastIvl`, `factor`, `time`, `type`

---

## Graphical Actions

Control the Anki GUI. These actions open windows and navigate the interface.

| Action | Description | Key Params |
|--------|-------------|------------|
| `guiBrowse` | Open card browser with query | `query` (search string) |
| `guiSelectCard` | Select a card in the browser | `card` (card ID) |
| `guiSelectedNotes` | Get IDs of selected notes in browser | (none) |
| `guiAddCards` | Open Add Cards dialog | `note: {deckName, modelName, fields, tags}` (optional pre-fill) |
| `guiAddNoteSetData` | Pre-fill Add Cards dialog | `note: {deckName, modelName, fields, tags}` |
| `guiEditNote` | Open note editor | `note` (note ID) |
| `guiCurrentCard` | Get the current review card info | (none) |
| `guiStartCardTimer` | Start/reset the card timer | (none) |
| `guiShowQuestion` | Show the question side | (none) |
| `guiShowAnswer` | Show the answer side | (none) |
| `guiAnswerCard` | Answer the current card | `ease` (1-4) |
| `guiUndo` | Undo the last action | (none) |
| `guiDeckOverview` | Navigate to deck overview | `name` (deck name) |
| `guiDeckBrowser` | Navigate to deck browser | (none) |
| `guiDeckReview` | Start review for a deck | `name` (deck name) |
| `guiImportFile` | Import a file | `path` (absolute file path) |
| `guiExitAnki` | Close Anki | (none) |
| `guiCheckDatabase` | Run database check | (none) |
| `guiPlayAudio` | Play audio on current card | (none) |

---

## Miscellaneous Actions

### requestPermission

Check API connectivity and request permission. Always call this first.

```bash
curl -s localhost:8765 -X POST -d '{"action": "requestPermission", "version": 6}'
```

**Returns:** `{permission: "granted", requireApikey: false, version: 6}`

### version

Get AnkiConnect version. No params. Returns integer.

### apiReflect

List available actions and their parameters for introspection.

**Params:** `scopes` — array of strings (e.g., `["actions", "actionParams"]`), `actions` — array of action names (optional filter)

### sync

Trigger synchronization with AnkiWeb. No params. Requires AnkiWeb account configured in Anki.

### getProfiles

List all Anki profiles. No params. Returns array of strings.

### getActiveProfile

Get the currently active profile name. No params. Returns string.

### loadProfile

Switch to a different profile.

**Params:** `name` — profile name

### multi

Execute multiple actions in a single request. Returns array of results.

```bash
curl -s localhost:8765 -X POST -d '{
  "action": "multi",
  "version": 6,
  "params": {
    "actions": [
      {"action": "deckNames"},
      {"action": "getTags"},
      {"action": "getNumCardsReviewedToday"}
    ]
  }
}'
```

**Params:** `actions` — array of `{action, version, params}` objects. Inner `version` is optional.

### exportPackage

Export a deck to an `.apkg` file.

**Params:** `deck` — deck name, `path` — output file path, `includeSched` — boolean

### importPackage

Import an `.apkg` file.

**Params:** `path` — absolute path to `.apkg` file

### reloadCollection

Reload the Anki collection from disk. No params.

---

## Search Query Syntax

Used by `findNotes` and `findCards`. Queries can combine multiple terms.

| Query | Description |
|-------|-------------|
| `deck:DeckName` | Notes in a specific deck |
| `deck:Parent::Child` | Notes in a sub-deck |
| `tag:tagname` | Notes with a specific tag |
| `tag:parent::child` | Notes with a hierarchical tag |
| `note:ModelName` | Notes of a specific type |
| `is:due` | Cards due for review |
| `is:new` | Cards never reviewed |
| `is:suspended` | Suspended cards |
| `is:buried` | Buried cards |
| `"field:value"` | Search a specific field |
| `added:N` | Cards added in last N days |
| `rated:N` | Cards reviewed in last N days |
| `rated:N:ease` | Cards with specific rating (1-4) in last N days |
| `prop:ivl>=30` | Cards with interval >= 30 days |
| `prop:due=0` | Cards due today |
| `prop:ease<2.5` | Cards with ease < 250% |
| `flag:N` | Cards with flag N (1-4) |
| `*` | All notes/cards |

**Combining queries:**
- Space between terms = AND: `deck:Spanish tag:verbs is:due`
- `OR` keyword: `tag:easy OR tag:beginner`
- `-` prefix = NOT: `deck:Spanish -tag:advanced`
- Parentheses for grouping: `(tag:easy OR tag:beginner) deck:Spanish`
- Quotes for exact match: `"front:exact phrase"`
