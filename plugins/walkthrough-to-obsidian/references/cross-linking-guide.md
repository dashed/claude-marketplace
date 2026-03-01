# Cross-linking Guide

Taxonomy of contextual cross-links to add between walkthrough pages. These transform a collection of pages into a richly connected knowledge graph.

## Link Priority

### High Value — Always Add

These links follow natural reading paths and significantly improve navigation.

#### Character/NPC → Quest References

When a character page mentions quests they give or are involved in, link to the specific quest heading.

```markdown
<!-- Before -->
Cain is responsible for giving you the "Archbishop Lazarus" and "Diablo" Quests.

<!-- After -->
Cain is responsible for giving you the [[Quests#Archbishop Lazarus|"Archbishop Lazarus"]] and [[Quests#Diablo|"Diablo"]] Quests.
```

#### Quest Rewards → Item Pages

When a quest rewards a unique or notable item, link to the item entry.

```markdown
<!-- Before -->
Your prize is the Butcher's Cleaver.

<!-- After -->
Your prize is the [[Unique Items#The Butcher's Cleaver|Butcher's Cleaver]].
```

#### Level/Area ↔ Quest Cross-references

- Level walkthrough pages mention which quests can be triggered → link to quest headings
- Quest pages mention which dungeon area they occur in → link to level pages

```markdown
<!-- Level page linking to quest -->
The Butcher can be found on this level. See [[Quests#The Butcher|The Butcher quest]].

<!-- Quest page linking to level -->
This quest occurs in the [[The Dungeon (Levels 1-4)|Dungeon]].
```

### Medium Value — Add When Natural

#### Spell/Ability Mentions → Spell Page

When spells are mentioned by name in other pages (Characters, Quests, Hints), link to the spell entry.

```markdown
<!-- Before -->
Use Town Portal to escape quickly.

<!-- After -->
Use [[Spells#Town Portal|Town Portal]] to escape quickly.
```

#### Boss/Monster Mentions → Bestiary

Link notable boss or monster names to the bestiary page.

```markdown
<!-- Before -->
The Succubi are the deadliest enemies in Hell.

<!-- After -->
The [[Bestiary|Succubi]] are the deadliest enemies in Hell.
```

If individual monsters have their own headings, use heading anchors:
```markdown
[[Bestiary#Succubi|Succubi]]
```

#### Quest Page → NPC References

Link NPC names mentioned in quest descriptions back to the character/town page.

```markdown
<!-- Before -->
Speak to Griswold to receive your reward.

<!-- After -->
Speak to [[Town of Tristram#Griswold the Blacksmith|Griswold]] to receive your reward.
```

### Lower Value — Add Selectively

#### Shrine Effects → Spells

When shrine descriptions reference specific spells, link to the spell entry.

```markdown
<!-- Before -->
Casts Nova in every direction.

<!-- After -->
Casts [[Spells#Nova|Nova]] in every direction.
```

#### "See Also" Cross-references

Add bidirectional "See also" lines between related reference pages:

```markdown
> **See also:** [[Unique Items|Unique Items]]
```

Good candidates for "See also":
- Item Prefixes/Suffixes ↔ Unique Items
- Bestiary ↔ Level walkthrough pages
- Spells ↔ Characters (class abilities)
- Lore ↔ Quest pages

## Rules

### Link the First Mention Only

Within each section (quest, character, tip), only link the first meaningful mention of a name. Repeated links feel cluttered.

```markdown
<!-- Good: first mention linked -->
Use [[Spells#Town Portal|Town Portal]] to return to town. Once through the Town Portal, sell your items.

<!-- Bad: every mention linked -->
Use [[Spells#Town Portal|Town Portal]] to return. Once through the [[Spells#Town Portal|Town Portal]], sell items.
```

### Use Aliases to Keep Text Natural

Never change the visible text. Use wiki-link aliases:

```markdown
<!-- Good -->
[[Town of Tristram#Griswold the Blacksmith|Griswold]]

<!-- Bad — changes the author's text -->
[[Town of Tristram#Griswold the Blacksmith]]
```

### Verify Heading Names Before Linking

Always read the target page first to confirm the exact heading text. Obsidian heading anchors are case-sensitive and must match exactly.

```markdown
<!-- The heading is "## Cain the Elder", so the anchor is: -->
[[Town of Tristram#Cain the Elder|Cain]]

<!-- NOT -->
[[Town of Tristram#Cain|Cain]]  <!-- This won't work -->
```

### Don't Overlink

Skip a link if:
- The reference is too generic (e.g., "the dungeon" in casual context)
- It would interrupt the reading flow
- The linked page doesn't add useful context for that mention
- The section already has many links and adding more would feel cluttered

### Escape Pipes in Tables

When adding wiki-links inside markdown tables, escape the pipe character:

```markdown
| NPC | Quest |
| --- | ----- |
| [[Tristram#Cain\|Cain]] | [[Quests#Diablo\|Diablo]] |
```

## Parallelization Strategy

Split cross-linking work by which pages each agent **modifies** (not reads):

- **Agent 1**: Character/NPC pages + Level walkthrough pages
- **Agent 2**: Quest page (largest, gets its own agent)
- **Agent 3**: Reference pages (Spells, Shrines, Bestiary, Items, etc.)

Each agent must **read** the target pages to get exact heading names, but only **modifies** their assigned pages. This prevents edit conflicts.
