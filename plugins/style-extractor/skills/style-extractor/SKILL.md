---
name: style-extractor
description: "Extract and document writing styles from source texts into reusable style guides. Use when the user wants to analyze an author's voice, create a style guide from a book or document, capture writing patterns for replication, or build a writing style rubric. Triggers on 'extract style', 'analyze writing style', 'capture voice', 'style guide from', or 'writing style analysis'."
---

# Style Extractor

Extract reusable writing style guides from any source text. Produces four standardized deliverables that capture general patterns — not copied phrases — so the style can be replicated for any topic.

## When to Use

- User asks to extract or analyze a writing style from a book, article, or document
- User wants to replicate an author's voice for new content
- User wants a style guide, voice card, or writing rubric from a source text
- User says "extract style from...", "analyze the writing style of...", or "capture this voice"

## Prerequisites

**MCP tools required:**
- `mcp__fuzzy-search` — PDF page counting, outline extraction, and page-level reading
- `mcp__sequential-thinking__sequentialthinking` — Structured analysis across dimensions

**Output location:** `writing-styles/<style-name>/` in the project root. See `writing-styles/README.md` for the collection structure and `writing-styles/_template/` for deliverable templates.

## Workflow

### Phase 1: Source Analysis

Identify the source text and assess its structure before reading.

**For PDFs:**

1. Get page count: `mcp__fuzzy-search__get_pdf_page_count`
2. Get outline/TOC: `mcp__fuzzy-search__get_pdf_outline`
3. Understand document structure before sampling

**Select 5–7 sampling points** distributed across the text:

| Sample | Location | Why |
|--------|----------|-----|
| Opening | First 10% | Capture introductory voice, setup patterns |
| Early-middle | 25–35% | Style settles after opening |
| Middle | 45–55% | Core voice, least influenced by beginning/ending effects |
| Late-middle | 65–75% | Check for drift or adaptation |
| End | 85–95% | Closing patterns, evolved voice |
| +1–2 optional | Varied | Specific chapters, asides, or structurally distinct sections |

**Read representative passages** using `mcp__fuzzy-search__extract_pdf_pages` or the Read tool. Aim for ~50–80 pages total across all samples.

**For non-PDF files:** Use the Read tool directly. Apply the same sampling distribution across the document's length.

### Phase 2: Dimension Extraction

Analyze **17 style dimensions** across all sampled passages. Use `mcp__sequential-thinking__sequentialthinking` to organize observations systematically.

| # | Dimension | What to look for |
|---|-----------|-----------------|
| 1 | Tone | Formal/informal, serious/playful, authoritative/conversational |
| 2 | Sentence length & structure | Average length, variation, complexity, use of fragments |
| 3 | Paragraph length & density | Short punchy vs. long expository, information density |
| 4 | Vocabulary level & register | Technical depth, word choice patterns, jargon usage |
| 5 | Transitions | How sentences, paragraphs, and sections connect |
| 6 | Humor & personality | Wit, asides, self-deprecation, enthusiasm markers |
| 7 | Directness | Hedging vs. assertion, qualification patterns |
| 8 | Emotional warmth | Distance vs. intimacy, encouragement, empathy |
| 9 | Explanation structure | Top-down vs. bottom-up, example-first vs. definition-first |
| 10 | Opening patterns | How sections/chapters begin, hooks, framing devices |
| 11 | Closing patterns | How sections end, callbacks, forward references |
| 12 | Punctuation habits | Em dashes, semicolons, parentheticals, ellipses, exclamation marks |
| 13 | Rhetorical moves | Analogies, rhetorical questions, repetition, contrast pairs |
| 14 | Reader address | Pronouns (we/you/one), assumed relationship, direct address |
| 15 | Use of examples | Frequency, placement, concrete vs. abstract, real vs. constructed |
| 16 | Historical/cultural references | Allusions, citations, name-dropping, assumed shared knowledge |
| 17 | Adaptive patterns | How style shifts with material difficulty, topic type, or audience |

Focus on **patterns, not content**. A style dimension describes HOW the author writes, never WHAT they write about.

For detailed guidance on analyzing each dimension, see [references/style-dimensions.md](references/style-dimensions.md).

### Phase 3: Synthesis

Generate four deliverables in `writing-styles/<style-name>/`:

| Deliverable | Path | Target Length | Purpose |
|-------------|------|---------------|---------|
| Full Style Guide | `style/full-style-guide.md` | 800–1500 words | Comprehensive analysis of all 17 dimensions |
| Voice Card | `style/voice-card.md` | ~300 words | One-page cheat sheet for quick reference |
| Do/Don't Checklist | `style/do-dont.md` | 20–30 items | Actionable guardrails for writing in this style |
| Style Rubric | `evals/style-rubric.md` | 5 dimensions | 1–5 scoring scale for evaluating style match |

**Every deliverable MUST include 2–3 examples** of neutral text rewritten in the extracted style. These examples demonstrate the style applied to content unrelated to the source.

Use `writing-styles/_template/` as the structural starting point for each file.

### Phase 4: Output

1. Create the folder structure:
   ```
   writing-styles/<style-name>/
   ├── style/
   │   ├── full-style-guide.md
   │   ├── voice-card.md
   │   └── do-dont.md
   └── evals/
       └── style-rubric.md
   ```

2. Write all four deliverables.

3. Verify the structure matches the template layout in `writing-styles/_template/`.

## Naming Convention

Use kebab-case: `<author-or-title>`

| Source | Directory Name |
|--------|---------------|
| *Mathematical Proofs* by Chartrand | `warm-academic-exposition` |
| Hemingway's short stories | `hemingway-short-stories` |
| Stripe API documentation | `stripe-api-docs` |
| Paul Graham's essays | `paul-graham-essays` |

## Best Practices

- **Sample broadly.** Pull from beginning, middle, AND end — styles evolve across a text.
- **Prioritize consistency.** Features that appear across multiple samples define the real style; one-off features are noise.
- **Track adaptation.** Note how style shifts for different material types, difficulty levels, or audiences. This is dimension 17 and often the most valuable.
- **Extract patterns, not phrases.** Never copy distinctive phrases as style rules. Identify the general pattern the phrase exemplifies.
- **Use agent teams for large texts.** Assign different sampling regions to different researchers, then synthesize.
- **Cross-validate.** If a pattern appears in only one sample, it may be a local anomaly — flag it but don't center the guide on it.

## Anti-Patterns

1. **Extracting content as style.** Topic-specific vocabulary is content, not style. "Uses the word 'eigenvalue'" is content; "introduces technical terms with an informal gloss" is style.
2. **Projecting absent features.** Don't claim humor if there is none. Don't invent warmth in clinical prose. Report what IS there.
3. **Sampling from one section only.** A single chapter gives a biased picture. The five-point sampling is non-negotiable.
4. **Copying signature phrases.** "Always use the phrase 'Let us consider...'" is wrong. "Opens explorations with an inclusive invitation" is right.
5. **Domain-locked guides.** A style guide that only works for the original domain has failed. The deliverables must transfer to any topic.

## References

For detailed analysis guidance and deliverable templates:

- [references/style-dimensions.md](references/style-dimensions.md) — Detailed analysis guide for each of the 17 dimensions with examples and scoring criteria
- [references/deliverable-templates.md](references/deliverable-templates.md) — Templates for all four deliverables with embedded guidance and worked examples
