# Writing Styles Collection

A curated collection of writing style guides, each extracted from a specific author or text. These guides enable consistent voice replication across any topic.

## Structure

Each style lives in its own directory:

```
writing-styles/
├── README.md                          # This file
├── _template/                         # Template for adding new styles
│   ├── style/
│   │   ├── full-style-guide.md        # Comprehensive style analysis
│   │   ├── voice-card.md              # 1-page quick reference
│   │   └── do-dont.md                 # Practical checklist
│   └── evals/
│       └── style-rubric.md            # 1-5 scoring rubric
├── warm-academic-exposition/           # First style entry
│   ├── style/
│   │   ├── full-style-guide.md
│   │   ├── voice-card.md
│   │   └── do-dont.md
│   └── evals/
│       └── style-rubric.md
└── <future-style>/                    # Add more here
```

## Files in Each Style

| File | Purpose | Length |
|------|---------|--------|
| `style/full-style-guide.md` | Comprehensive analysis of tone, structure, vocabulary, rhetorical patterns, and more | 800-1500 words |
| `style/voice-card.md` | One-page cheat sheet for quick reference | ~300 words |
| `style/do-dont.md` | Actionable checklist of what to do and avoid | 20-30 items |
| `evals/style-rubric.md` | Scoring rubric (1-5) for evaluating style match | 5 dimensions |

## Adding a New Style

1. Copy `_template/` to a new directory named `<author-or-text>/`
2. Read the source material, sampling from beginning, middle, and end
3. Fill in each template file with extracted patterns
4. Focus on **reusable patterns**, not copied phrases
5. Include 2-3 examples of neutral text rewritten in the style

## Current Styles

| Style | Source | Domain |
|-------|--------|--------|
| `warm-academic-exposition` | *Mathematical Proofs* (Chartrand et al., 4th ed.) | Warm, structured, rigorous-but-approachable teaching |

## Usage

Reference a style guide when writing content that should match a particular voice. The voice card provides a quick refresher; the full guide provides depth; the do/don't list catches common mistakes; the rubric scores output quality.
