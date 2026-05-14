# Card Design Reference

Effective flashcard design is the single biggest factor in long-term retention. A well-designed card takes seconds to review and sticks for months. A poorly designed card wastes time and breeds frustration. This guide covers principles and patterns for creating cards that work.

## Table of Contents

- [Minimum Information Principle](#minimum-information-principle)
- [Card Types and When to Use Each](#card-types-and-when-to-use-each)
- [Writing Effective Questions](#writing-effective-questions)
- [Cloze Deletion Patterns](#cloze-deletion-patterns)
- [Tagging Strategies](#tagging-strategies)
- [Deck Organization](#deck-organization)
- [Media in Cards](#media-in-cards)
- [Common Anti-patterns](#common-anti-patterns)

---

## Minimum Information Principle

The most important rule in flashcard design: **one atomic fact per card**.

Cards that test a single, discrete piece of knowledge are faster to review, easier to grade honestly, and produce stronger memory traces. When a card bundles multiple facts, partial recall creates ambiguity — did you "know" it or not?

### Bad: Compound Card

```
Q: What are the SOLID principles?
A: Single Responsibility, Open/Closed, Liskov Substitution,
   Interface Segregation, Dependency Inversion
```

This card tests recall of a list. If you forget one item, the whole card fails. If you remember four out of five, you can't honestly mark it as correct.

### Good: Atomic Cards

Split into individual cards:

```
Q: In SOLID, what does the "S" stand for?
A: Single Responsibility Principle

Q: What does the Single Responsibility Principle state?
A: A class should have only one reason to change.

Q: In SOLID, what does the "O" stand for?
A: Open/Closed Principle
```

Each card tests exactly one fact. You can accurately track which concepts you know and which need more practice.

### When to Split

- **Lists** — one card per item, with context for which list it belongs to
- **Processes** — one card per step, or use cloze deletions on a sequence
- **Comparisons** — separate cards for each dimension of comparison
- **Definitions with multiple parts** — one card per clause or property

### When NOT to Split

- The items are meaningless in isolation (e.g., a chemical formula is one unit)
- The fact is genuinely atomic already (a date, a name, a single property)

---

## Card Types and When to Use Each

### Basic (Front/Back)

The standard question-and-answer format. One side poses a question, the other reveals the answer.

```
Front: What is the time complexity of binary search?
Back:  O(log n)
```

**Best for:**
- Definitions and terminology
- Single-fact recall (dates, names, values)
- "What is X?" or "What does X do?" questions
- Conceptual questions with short answers

### Basic (and Reversed Card)

Creates two cards automatically — one in each direction. If you create a card with Front A and Back B, Anki generates both A→B and B→A.

```
Card 1 — Front: "ephemeral"  →  Back: "lasting for a very short time"
Card 2 — Front: "lasting for a very short time"  →  Back: "ephemeral"
```

**Best for:**
- Vocabulary and translations (word ↔ definition)
- Symbol/abbreviation mappings (HTTP → HyperText Transfer Protocol)
- Bidirectional associations where recall in both directions matters

**Avoid when:**
- The reverse direction produces an ambiguous question
- Only one direction of recall is useful

### Cloze Deletion

Fill-in-the-blank format. Anki hides the cloze-marked text and asks you to recall it from context.

```
{{c1::TCP}} operates at the {{c2::transport}} layer of the OSI model.
```

This generates two cards:
- Card 1: `[...]` operates at the transport layer of the OSI model. → TCP
- Card 2: TCP operates at the `[...]` layer of the OSI model. → transport

**Best for:**
- Facts embedded in sentences
- Formulas and equations
- Sequences and processes
- Code syntax patterns
- Anything where surrounding context aids recall

### Choosing the Right Type

| Scenario | Recommended Type |
|----------|-----------------|
| Term → Definition | Basic |
| Word ↔ Translation | Basic (and reversed) |
| Formula with variables | Cloze |
| Code syntax pattern | Cloze |
| Historical date | Basic |
| Process steps in order | Cloze |
| Symbol ↔ Meaning | Basic (and reversed) |
| Concept explanation | Basic |

---

## Writing Effective Questions

### Be Specific and Unambiguous

Every card should have exactly one correct answer. If the question could reasonably be answered multiple ways, it needs to be more specific.

**Bad:**
```
Q: What is Python?
A: A programming language
```
(Too vague — could answer "a snake", "a Monty Python reference", etc.)

**Better:**
```
Q: What type of language is Python (compiled vs. interpreted)?
A: Interpreted
```

### Use Context Cues

Provide enough context that the question has a clear scope. Prefix with the domain, topic, or framework.

**Bad:**
```
Q: What does `map` return?
A: A new array with transformed elements
```
(Which language? `map` exists in many contexts.)

**Better:**
```
Q: In JavaScript, what does Array.prototype.map() return?
A: A new array with the results of calling the provided function on every element
```

### Avoid Yes/No Questions

Yes/no questions test recognition, not recall. They're easy to guess and don't build strong memories.

**Bad:**
```
Q: Is quicksort stable?
A: No
```

**Better:**
```
Q: What is the stability of quicksort?
A: Unstable — equal elements may change relative order
```

**Also good (rephrase as "which" or "what"):**
```
Q: Which common O(n log n) sorting algorithms are unstable?
A: Quicksort, heapsort
```

### Test Understanding, Not Recognition

Cards should require you to produce an answer from memory, not just recognize a familiar pattern.

**Bad:**
```
Q: The CAP theorem states that a distributed system can guarantee
   at most two of: Consistency, _____, Partition tolerance
A: Availability
```
(Just pattern-matching a familiar phrase.)

**Better:**
```
Q: You're designing a distributed database that must handle network partitions.
   According to the CAP theorem, what trade-off must you make?
A: Choose between consistency and availability — you cannot guarantee both
   during a partition.
```

### Additional Tips

- **Front-load the question** — put the most important context word first
- **Keep answers short** — if the answer is a paragraph, the card is testing too much
- **Use examples** — "Give an example of X" cards build deeper understanding
- **Ask "why" and "how"** — not just "what", to test deeper comprehension

---

## Cloze Deletion Patterns

### Single Cloze

The simplest form. One blank per card.

```
The {{c1::mitochondria}} is the powerhouse of the cell.
```

Generates one card with "mitochondria" hidden.

### Multiple Clozes, Same Card

Use the same cloze number to hide multiple items on a single card. The reviewer must recall all blanks at once.

```
The {{c1::git add}} command stages files, and {{c1::git commit}} saves them.
```

Generates one card with both "git add" and "git commit" hidden simultaneously.

**Use when:** The items are closely related and recalling one without the other isn't meaningful.

### Overlapping Clozes, Separate Cards

Use different cloze numbers to generate separate cards from the same note. Each card hides only its numbered cloze.

```
{{c1::HTTP}} uses port {{c2::80}} by default, while {{c3::HTTPS}} uses port {{c4::443}}.
```

Generates four cards, each hiding one blank while showing the rest.

**Use when:** Each piece of information is independently worth testing.

### Best Practices for Cloze Content

**Do:**
- Keep the surrounding sentence meaningful — the context should genuinely help recall
- Cloze the important part, not the filler
- Use clozes for content that naturally fits in a sentence or formula

**Don't:**
- Cloze so much text that there's no context left
- Use clozes as a lazy alternative to writing a proper question
- Create clozes where the blank could be filled by many valid answers

**Bad cloze:**
```
{{c1::Python}} is a {{c2::programming language}} created by {{c3::Guido van Rossum}}.
```
(c2 is trivially obvious from context; c1 could be many languages.)

**Good cloze:**
```
Python was created by {{c1::Guido van Rossum}} and first released in {{c2::1991}}.
```
(Both blanks have unique, specific answers aided by context.)

### Cloze with Code

Clozes work well for syntax and API patterns:

```
In Python, use {{c1::enumerate()}} to loop over a list with both index and value.
```

```
The SQL clause {{c1::HAVING}} filters groups after {{c2::GROUP BY}} aggregation.
```

---

## Tagging Strategies

Tags in Anki provide flexible, cross-cutting organization that complements the deck hierarchy.

### Use Tags For

- **Topics and concepts**: `recursion`, `sorting`, `dynamic-programming`
- **Source material**: `source::textbook-ch3`, `source::lecture-2025-01-15`
- **Difficulty level**: `difficulty::hard`, `difficulty::easy`
- **Status**: `needs-review`, `needs-image`, `leech`
- **Exam or goal**: `exam-2025-final`, `certification::aws-saa`

### Tag Naming Conventions

- Use lowercase with hyphens: `binary-search`, not `BinarySearch`
- Use `::` for tag hierarchies: `language::python::stdlib`
- Keep tags short but descriptive
- Be consistent — decide on a convention and stick with it

### Tag Hierarchy Examples

```
topic::algorithms::sorting
topic::algorithms::graph
topic::data-structures::trees
topic::data-structures::hash-tables

source::book::clean-code
source::course::cs50
source::documentation::mdn

status::needs-review
status::needs-media
status::suspended
```

### Tags vs. Decks

| Concern | Use Tags | Use Decks |
|---------|----------|-----------|
| Primary subject area | | X |
| Cross-cutting topic | X | |
| Source material | X | |
| Difficulty level | X | |
| Exam preparation | X | |
| Study schedule grouping | | X |

A card lives in exactly one deck but can have unlimited tags. Use decks for structure, tags for metadata.

---

## Deck Organization

### The `::` Separator

Anki uses `::` to create sub-deck hierarchies. Reviewing a parent deck includes all child decks.

```
Computer Science
Computer Science::Algorithms
Computer Science::Algorithms::Sorting
Computer Science::Algorithms::Graph Theory
Computer Science::Data Structures
Computer Science::Data Structures::Trees
Computer Science::Data Structures::Hash Tables
```

### Guidelines

**Keep it shallow** — 2-3 levels maximum. Deep nesting creates navigation overhead and fragments your review sessions.

```
# Good: 2 levels
Mathematics::Linear Algebra
Mathematics::Calculus

# Bad: 5 levels
University::Year 3::Semester 1::CS 301::Week 5
```

**Organize by subject, not by source** — structure decks around what you're learning, not where you learned it.

```
# Good
Spanish::Vocabulary
Spanish::Grammar

# Bad
Spanish::Duolingo Lessons
Spanish::Textbook Chapter 3
```
(Use tags for source tracking instead.)

**One deck per study domain** — if you'd study the topics in the same session, they belong in the same deck or parent deck.

**Avoid single-card decks** — if a deck has fewer than 10-20 cards, it probably belongs as a tag or as part of a broader deck.

---

## Media in Cards

### When to Use Images

- **Diagrams and charts** — architecture diagrams, flowcharts, data visualizations
- **Visual concepts** — anatomy, geography, UI components
- **Code output** — terminal screenshots, rendered HTML
- **Mnemonics** — visual memory aids

### When to Use Audio

- **Language learning** — pronunciation, listening comprehension
- **Music theory** — intervals, chord recognition
- **Phonetics** — sound distinctions

### Media with AnkiConnect

AnkiConnect provides the `storeMediaFile` action to add media to Anki's collection:

```json
{
  "action": "storeMediaFile",
  "version": 6,
  "params": {
    "filename": "diagram_binary_tree.png",
    "data": "<base64-encoded-data>"
  }
}
```

Alternatively, provide a URL for Anki to download:

```json
{
  "action": "storeMediaFile",
  "version": 6,
  "params": {
    "filename": "diagram_binary_tree.png",
    "url": "https://example.com/diagram.png"
  }
}
```

Reference the file in card fields using standard HTML:

```html
<img src="diagram_binary_tree.png">
```

### Media Best Practices

- **Name files descriptively** — `diagram_binary_tree.png`, not `img001.png`
- **Keep file sizes reasonable** — large media slows syncing across devices
- **Don't rely solely on media** — add text context so the card works even if the media fails to load
- **Use alt text** — `<img src="file.png" alt="Binary tree with 7 nodes">` aids accessibility

---

## Common Anti-patterns

### 1. The Encyclopedia Card

**Problem:** Cards with paragraph-length answers that take 30+ seconds to review.

```
Q: Explain how TCP's three-way handshake works.
A: First, the client sends a SYN packet to the server with an initial
   sequence number. The server responds with a SYN-ACK packet, acknowledging
   the client's sequence number and providing its own. Finally, the client
   sends an ACK packet confirming the server's sequence number, and the
   connection is established. This ensures both sides agree on initial
   sequence numbers and are ready to communicate...
```

**Fix:** Break into atomic cards — one per step, one for the purpose, one for the packet types.

### 2. Memorizing Without Understanding

**Problem:** Creating cards for material you don't yet understand. Rote memorization without comprehension leads to fragile knowledge that can't be applied.

**Fix:** Study the material first. Understand it. Then create cards to retain what you've understood. Cards reinforce knowledge — they don't build it.

### 3. The Daily Avalanche

**Problem:** Adding 50+ new cards per day, then drowning in reviews within a week.

**Fix:** Limit new cards to 10-20 per day. Anki's scheduling means reviews compound — 20 new cards/day creates a sustainable ~100-200 reviews/day workload. 50 new cards/day quickly becomes 500+ daily reviews.

### 4. No Tags or Organization

**Problem:** Dumping all cards into a single "Default" deck with no tags. Impossible to find, filter, or selectively study.

**Fix:** Use a simple deck hierarchy for major subjects and tags for everything else. Even minimal organization (`topic::X`, `source::Y`) pays dividends.

### 5. Trick Questions

**Problem:** Cards designed to be tricky or catch you out, rather than test genuine knowledge.

```
Q: What's the difference between == and === in Python?
A: Trick question — Python doesn't have ===
```

**Fix:** Cards should test real knowledge. If the distinction matters (like `==` vs `===` in JavaScript), test it directly.

### 6. Copy-Paste Cards

**Problem:** Copying text verbatim from a textbook without reformulating it in your own words.

**Fix:** Rephrase in your own language. The act of reformulation itself strengthens understanding, and cards written in your own voice are easier to review.

### 7. Neglecting Reviews

**Problem:** Creating lots of cards but skipping daily reviews. The entire system depends on reviewing cards at the scheduled intervals.

**Fix:** Anki works through consistent daily use. Even 10 minutes per day is more effective than sporadic hour-long sessions. Build the habit before building the collection.
