---
name: long-form-math
description: "Write mathematics in a long-form, understanding-focused style with detailed proofs and rich exposition. Use when explaining mathematical concepts, writing proofs, tutoring math, creating educational math content, or when the user asks for mathematical explanations. Inspired by Jay Cummings' Real Analysis and Chartrand's Mathematical Proofs. Triggers on proof writing, theorem explanations, mathematical exposition, or math tutoring."
---

# Long-Form Mathematics

Write mathematics the way the best textbooks do: with motivation, intuition, scratch work, and post-proof reflection. Every proof tells a story. Every definition earns its place.

## When to Use

- Writing or explaining proofs
- Introducing mathematical definitions, theorems, or concepts
- Tutoring someone in mathematics
- Creating educational math content (lecture notes, textbook-style explanations)
- Answering "why" questions about mathematical results
- Working through problem sets with a student

## Core Philosophy

| Principle | Meaning |
|-----------|---------|
| Understanding over economy | A longer explanation that builds understanding beats a terse proof that sacrifices clarity |
| Show the thinking | Make the invisible reasoning process visible -- scratch work, false starts, technique selection |
| Words between symbols | Never present bare equation chains; every step gets connective text explaining WHY |
| Math is communication | Writing quality matters as much as correctness; the reader must be convinced AND enlightened |

## Proof Writing Workflow

Every proof follows three phases. Do not skip phases 1 and 3.

### Phase 1: Pre-Proof Strategy

Before writing the proof, show the reader how the proof was discovered.

**Scratch Work.** Work backward from the desired conclusion. Show the exploratory reasoning that reveals what to prove and how. Label this section explicitly.

> Example: "We want to show |a_n - 0| < e. Unraveling, this means 1/n < e, so n > 1/e. This tells us to pick N = ceil(1/e)."

**Technique Selection.** State which proof technique to use and WHY.

| Try this technique... | When... |
|----------------------|---------|
| Direct proof | The hypothesis gives enough structure to reach the conclusion |
| Contrapositive | The hypothesis yields a complicated expression; starting from ~Q is simpler |
| Contradiction | The result sounds "negative" (no, never, impossible, does not exist) |
| Construction | The result asserts existence ("there exists...") |
| Cases | The domain splits naturally (even/odd, positive/negative/zero) |
| Both directions | The result is biconditional ("if and only if") |

**Proof Idea.** For long proofs, give a plain-English summary of the high-level strategy before diving into details.

> Example: "The idea is to show |a - b| < e for all e > 0, forcing |a - b| = 0."

### Phase 2: The Proof

Write the polished proof following these structural rules:

1. **State assumptions first.** Open with "Assume that..." or "Let... be..."
2. **Type every variable.** When introducing k, say "where k is an integer." Never leave a variable untyped.
3. **Justify each step.** Explain WHY each step is taken, not just WHAT happens. Use phrases like "By [theorem]...", "Since [established fact]...", "By definition of..."
4. **Words between equations.** Connect every equation to the next with explanatory text. Vary transitional words: therefore, thus, hence, consequently, so, it follows that.
5. **Conclude explicitly.** End by stating what has been shown: "Therefore n^2 is even, as desired."

**Correct pattern:**

> Since x is even, we can write x = 2k for some integer k. Then x^2 = (2k)^2 = 4k^2 = 2(2k^2). Since 2k^2 is an integer, it follows that x^2 is even.

**Incorrect pattern:**

> x = 2k
> x^2 = 4k^2 = 2(2k^2)
> Therefore x^2 is even.

The incorrect version is a bare equation chain with no connective text and no typing of variables.

### Phase 3: Post-Proof Analysis

After the proof, reflect on it.

- **The Moral.** State what the result teaches us in plain English. ("The moral: two sets can have the same size even though one is a proper subset of the other.")
- **Could it be simpler?** If a more elegant proof exists, show it.
- **Alternative approaches.** If a different technique illuminates a different aspect, present it.
- **Reverse engineering.** Show how the polished proof was constructed from scratch work -- how we went from goal-backward exploration to hypothesis-forward presentation.

## Exposition Patterns

When introducing a new topic or definition, follow this sequence:

### The Introduction Sequence

```
Motivating problem  -->  Intuition  -->  Formal definition  -->  Examples + Non-examples
```

1. **Motivating problem first.** Open with a paradox, puzzle, question, or historical problem that creates NEED for the concept. Never open with a bare definition.

   > "So, what do you think? Does slow and steady win the race? Zeno's paradox tells us..."

2. **Intuition before formalism.** Give the informal idea first. Build understanding of what the definition captures before stating it precisely.

   > "What the definition means is that eventually the points get 'arbitrarily close' to a."

3. **Formal definition.** Now state the precise definition. The reader is ready for it.

4. **Examples and non-examples.** Immediately follow with concrete examples that satisfy the definition AND examples that fail it, explaining why they fail.

   > "The integers Z almost form a field; they only fail the second half of Axiom 5."

### Additional Exposition Techniques

- **Questions that drive investigation.** Pose numbered questions that structure sections around intellectual curiosity. ("Does there exist a function continuous at one point but not at another?")
- **Historical storytelling.** Weave mathematical history into the exposition as narrative, not sidebar decoration. The story of Hippasus and the irrationals, Cantor and infinity, Archimedes and exhaustion -- these ARE the exposition.
- **Progressive disclosure.** Reference future topics: "We will come back to this." Build concepts incrementally. State a "moral" after each result, with each moral slightly more surprising than the last.
- **The almost-correct proof.** Show a proof attempt that fails, diagnose WHY it fails, then fix it. This teaches more than a perfect proof alone.
- **Investigation tables.** Create tables with "???" entries that get filled in as the exposition progresses, giving the reader an ongoing investigation to follow.

## Mathematical Writing Rules

Quick reference for clean mathematical prose. These rules apply to ALL mathematical writing in this style.

### Symbol Rules

| Rule | Bad | Good |
|------|-----|------|
| Never start a sentence with a symbol | "x^2 - 6x + 8 = 0 has two roots." | "The equation x^2 - 6x + 8 = 0 has two roots." |
| Separate adjacent symbols with words | "With the exception of a, b is the only root." | "With the exception of a, the number b is the only root." |
| Use words, not logical shorthand | "forall x, exists y s.t. ..." | "For every x, there exists a y such that..." |
| Explain every new symbol | "Then n = 2k + 1." | "Then n = 2k + 1, where k is an integer." |
| Use frozen symbols conventionally | Using m for a function | Use m, n for integers; f, g for functions; A, B for sets |
| Use consistent symbol families | "x = 2a and y = 2r" | "x = 2a and y = 2b" (or "x = 2r and y = 2s") |

### Language Rules

| Rule | Bad | Good |
|------|-----|------|
| Use "we" as default pronoun | "I will now show..." | "We will now show..." |
| Avoid "clearly/obviously" | "Clearly, n^2 is positive." | "Since n is nonzero, n^2 is positive." |
| Use "each/every" not "any" | "For any integer n..." | "For every integer n..." |
| Never use "Since...then" | "Since n is odd, then n^2 is odd." | "Since n is odd, it follows that n^2 is odd." |
| "Since" = established fact | "If n is odd" (when n is already known odd) | "Since n is odd" (for established facts) |
| Vary connective words | "Therefore... Therefore... Therefore..." | "Therefore... Thus... It follows that... Hence..." |
| Write complete sentences | Bare equation with no punctuation | Every equation is part of a sentence, ending with a period |

### Formatting Rules

- **Inline vs. display:** Short expressions inline; long expressions as centered displays.
- **Line breaks:** When breaking an expression, end the first line with the operator (+, -, =, <).
- **Alignment:** In multi-step computations, align equal signs vertically.
- **Variable reuse:** Never reuse the same variable for different quantities in the same proof. (Do NOT write "a = 2k and b = 2k" when a and b may differ.)

## Tone Guide

Write in a voice that is conversational yet precise, enthusiastic yet rigorous.

| Element | How to apply |
|---------|-------------|
| Direct address | Talk to the reader: "So, what do you think?" / "Bear with me." / "You will thank me later." |
| Rhetorical questions | Engage the reader in thinking before providing answers |
| Enthusiasm | "Make sure you take a moment to appreciate how wonderfully weird this is." |
| Encouragement | Acknowledge difficulty while motivating persistence: "This is subtle, but we will work through it." |
| Humor | Appropriate wit, especially in asides. Never at the expense of clarity. |
| Precision | Casual phrasing is fine; imprecise mathematics is not. Every informal statement must be backed by rigor when it matters. |

## Anti-Patterns

Do NOT do any of the following:

1. **Terse proofs that skip motivation.** Never write "The proof is left as an exercise" or present a proof without pre-proof strategy.
2. **Bare equation chains.** Never present a sequence of equations without words connecting them.
3. **Definitions before intuition.** Never open a topic with a formal definition. Motivate first.
4. **"Clearly" or "obviously."** These words cover up missing reasoning. Either provide the reasoning or omit the qualifier.
5. **Untyped variables.** Never introduce a variable without stating its type ("where k is an integer").
6. **Proof by example for universal statements.** Showing a result for n = 3 does not prove it for all n.
7. **Starting sentences with symbols.** Always begin with a word.
8. **Logical shorthand in exposition.** Replace all occurrences of "forall", "exists", "s.t.", "=>", "iff" with English words in finished writing.
9. **Assuming what you want to prove.** The conclusion cannot appear as a hypothesis.
10. **Reusing variables for different quantities.** If a = 2k and b is also even, write b = 2m, not b = 2k.

## References

For detailed examples and extended guidance:

- [references/proof-writing-guide.md](references/proof-writing-guide.md) -- Proof templates, worked examples for each technique, the three-phase pattern in full detail
- [references/exposition-patterns.md](references/exposition-patterns.md) -- Definition introduction sequences, motivating problems, investigation tables, progressive disclosure examples
