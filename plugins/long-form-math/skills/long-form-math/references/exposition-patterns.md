# Exposition Patterns for Long-Form Mathematics

A comprehensive reference for writing mathematical exposition that engages, motivates, and builds understanding. Distilled from Cummings' *Real Analysis: A Long-Form Textbook* and Chartrand's *Mathematical Proofs: A Transition to Advanced Mathematics*.

---

## Table of Contents

1. [The Motivation-First Pattern](#1-the-motivation-first-pattern)
2. [Definition Introduction Workflow](#2-definition-introduction-workflow)
3. [Building Intuition Before Formalism](#3-building-intuition-before-formalism)
4. [Historical Storytelling Integration](#4-historical-storytelling-integration)
5. [Questions That Drive Investigation](#5-questions-that-drive-investigation)
6. [Progressive Disclosure](#6-progressive-disclosure)
7. [Mathematical Writing Quality](#7-mathematical-writing-quality)
8. [Tone and Voice](#8-tone-and-voice)
9. [Anti-Patterns in Mathematical Exposition](#9-anti-patterns-in-mathematical-exposition)

---

## 1. The Motivation-First Pattern

Every mathematical topic should begin with a reason to care. Before definitions, before theorems, before any formalism, the reader needs a *problem* that creates genuine intellectual need for the concept that follows.

### The Core Principle

Open every topic with a motivating problem, paradox, question, or historical puzzle that makes the reader *want* the concept you are about to introduce. The motivation is not decoration placed before the "real" content. The motivation IS the entry point into the content.

### Examples from Cummings

**Zeno's paradox opens the study of limits and series (Ch. 1):**

> "So, what do you think? Does slow and steady win the race? It does seem paradoxical; our senses and life experiences tell us that this is obviously gibberish, but then again Zeno was a pretty smart guy, and his arguments do seem fairly logical and sound... So we have a challenge in front of us. When seemingly-good reasoning leads to a false conclusion, some part of our thinking must be wrong."

The paradox creates a tension the reader needs to resolve. The resolution -- that infinite sums can converge -- requires the machinery of the entire chapter. One hundred pages later, the reader finally has the tools to answer the opening question.

**Hilbert's Hotel opens the study of cardinality (Ch. 2):**

The hotel scenario escalates: one guest arrives, two guests, then infinitely many guests arrive. At each stage, the reader is asked to think about how to accommodate them. The escalating impossibility creates the need for a rigorous definition of "same size" for infinite sets.

**Archimedes and the circle open integration (Ch. 8):**

> "I've heard Archimedes be referred to as history's first true math nerd. He loved math. He reportedly would become so engrossed in his geometry that he would forget to eat or bathe..."

The method of exhaustion -- approximating a circle's area with polygons -- is presented as a 2,000-year-old puzzle that motivates the formal definition of the integral.

**A meme opens the study of continuity (Ch. 6):**

A progression of increasingly formal definitions, from "A function is continuous if it's like x^2" through "If you can draw it without picking up your pencil" all the way to the epsilon-delta definition. The humor frames the chapter's goal: making the intuitive rigorous.

### The Motivation-First Template

Use this structure when introducing a new topic:

```
1. HOOK: Present a paradox, puzzle, surprising fact, or historical problem.
   - Make the reader feel the tension or surprise directly.
   - Ask them to think about it: "So, what do you think?"

2. QUESTION: Sharpen the hook into a precise question.
   - "Can an infinite sum be finite?"
   - "Can two infinite sets have different sizes?"
   - "Does there exist a function continuous everywhere but differentiable nowhere?"

3. BRIDGE: Connect the question to the mathematics that follows.
   - "We'll develop the tools to answer this."
   - "It will take over a hundred pages before we fully understand why
     Zeno was mistaken, but we'll get there."

4. BEGIN: Start the formal exposition, now that the reader has a reason to care.
```

### When to Use Each Type of Hook

| Hook Type | Best For | Example |
|-----------|----------|---------|
| Paradox | Concepts that defy intuition | Zeno's paradox for convergence |
| Surprising fact | Results the reader won't believe | "There are as many rationals as integers" |
| Historical problem | Ancient concepts with modern formalization | Archimedes for integration |
| Practical question | Applied topics | "How do we compute areas of irregular shapes?" |
| Escalating scenario | Building complexity gradually | Hilbert's Hotel for cardinality |
| Humor / meme | Lightening heavy formalism | Continuity definition progression |

### What Makes a Good Motivation

- It should feel genuinely unresolved. If the reader already knows the answer, the motivation falls flat.
- The resolution should require the mathematics you are teaching (not just a clever argument).
- It should be accessible: the reader should understand the problem even if they cannot yet solve it.
- It should connect to the reader's experience or intuition, so they feel the surprise personally.

---

## 2. Definition Introduction Workflow

Definitions are the foundation of mathematical writing, and how you introduce them determines whether the reader internalizes or merely memorizes them. Never present a definition cold. Follow a five-step workflow.

### The Five Steps

**Step 1: Explain WHY this concept matters (motivation)**

Before the definition, explain the problem it solves or the gap it fills. The reader should feel the *need* for the definition before seeing it.

> "We are approaching the study of continuous functions. This is a surprisingly subtle task. In fact, there is a whole area of math devoted to the study of sets and continuous functions on those sets; this area is called topology." -- Cummings, before defining open sets

> "This idea may seem odd. It's not at all clear that this should be anything that we should care about. Bear with me, though, because in the grand scheme it is amazing how much this is exactly something that we should care about." -- Cummings, before defining compactness

**Step 2: Informal explanation using analogies and metaphors**

Give the reader a mental model before the symbols arrive.

- Sets as boxes: "Think of a set like a box. You can put things in it, take things out, look inside and see what's there. An empty box is still a box." (Cummings, p. 16)
- Convergence as "eventually close": "What the definition means is that eventually the points get 'arbitrarily close' to a. Maybe the first few points are not super close, but eventually they both get super close and stay super close." (Cummings, p. 71)
- Epsilon-neighborhoods as bands: A visual image of a horizontal band of width 2 epsilon around the limit, with sequence terms eventually staying inside the band.

**Step 3: Formal definition**

Now present the precise mathematical definition. By this point, the reader knows what to expect and can map the symbols to their existing mental model.

**Step 4: Examples (multiple, varied)**

Immediately follow with concrete examples that exercise the definition. Include:

- A simple, prototypical example (the one the definition was "designed for")
- An edge case or surprising example
- An example from a different context that shows the definition's breadth

Cummings on fields: Q is a field (expected). R is a field (expected). Z is NOT a field -- and here's exactly which axiom it fails.

Cummings on open sets: Five examples -- R is open, the empty set is open (with a delightful explanation of vacuous truth involving "purple elephants"), (a,b) is open, (a, infinity) is open, and [3,7] is NOT open.

**Step 5: Non-examples with explanation of WHY they fail**

Non-examples are at least as important as examples. They draw the boundary of the concept by showing what falls just outside.

Always explain *which part* of the definition fails and *why*.

> "The natural numbers N do not form a field; they fail the first half of Axiom 4 and both halves of Axiom 5."
> "The integers Z almost form a field; they only fail the second half of Axiom 5: For example, given a = 2, there is no integer a^{-1} such that 2 * a^{-1} = 1."

The word "almost" is doing important work here. It tells the reader how close Z comes and sharpens their understanding of exactly what a field requires.

### Complete Worked Example: Introducing Convergence

Here is the five-step workflow applied to the definition of sequence convergence:

**Step 1 (Motivation):** We have been working with sequences, computing their terms, and looking at patterns. But when we say a sequence "approaches" a value, what do we actually mean? Our intuition says the terms "get close" -- but how close? And when? We need a precise definition.

**Step 2 (Informal explanation):** Think of it this way: a sequence converges to a limit L if, no matter how small a target band you draw around L, eventually every term of the sequence lands inside that band and stays there. The first few terms can wander wherever they like. What matters is the tail.

**Step 3 (Formal definition):** A sequence (a_n) converges to a real number L if, for every epsilon > 0, there exists N in the natural numbers such that for every n > N, we have |a_n - L| < epsilon. We write a_n -> L.

**Step 4 (Examples):**
- The sequence a_n = 1/n converges to 0. Given epsilon > 0, choose N > 1/epsilon.
- The constant sequence a_n = 5 converges to 5 (every epsilon works with N = 1).
- The sequence a_n = (-1)^n / n converges to 0 (the terms alternate but shrink).

**Step 5 (Non-examples):**
- The sequence a_n = (-1)^n does NOT converge. It alternates between -1 and 1 forever. For epsilon = 0.5, no matter how large N is, there will always be terms outside the band around any proposed limit.
- The sequence a_n = n does NOT converge. The terms grow without bound; no finite L can serve as a limit.

### The Definition Introduction Template

```
MOTIVATION:  [1-2 paragraphs] Why do we need this concept?
             What gap does it fill? What problem does it solve?

INFORMAL:    [1 paragraph] Plain-English or visual explanation.
             Use analogies, metaphors, diagrams described in words.

DEFINITION:  [Formal statement] The precise mathematical formulation.

EXAMPLES:    [2-4 examples] Concrete instances that satisfy the definition.
             Vary the difficulty and context.

NON-EXAMPLES:[1-3 non-examples] Instances that FAIL the definition,
             with explicit identification of which condition fails.
```

---

## 3. Building Intuition Before Formalism

### The Core Rule

Always give the informal idea first, then the formal definition. Never the reverse.

This is perhaps the single most important exposition principle for long-form mathematics. When a reader encounters a formal definition they do not yet understand, they have nothing to attach it to -- the symbols float in a void. But when they first have an intuitive mental model, the formal definition becomes a sharpening of something they already grasp.

### Techniques for Building Intuition

**Visual and conceptual aids:**
- Epsilon-bands: "Imagine a horizontal band of width 2 epsilon centered at L. Convergence means the sequence terms eventually enter the band and never leave."
- Sets as boxes: Physical images of containers with objects inside, empty containers, containers inside containers.
- Functions as machines: Input goes in, output comes out.
- Open sets as neighborhoods: "Every point has some breathing room around it."

**Analogies and metaphors:**
- Compactness: "Every attempt to cover the set with open sets can be thinned down to a finite subcover." Think of it as a finiteness condition on an infinite-looking object.
- Uniform continuity vs. continuity: "Continuity says that at each point, there's a delta that works. Uniform continuity says there's a single delta that works everywhere simultaneously."

**Acknowledging strangeness:**
When a definition seems counterintuitive, say so directly. This validates the reader's confusion and builds trust.

> "It may seem crazy that this is one of the great definitions in mathematics, but it is." -- Cummings on compactness

> "Bear with me, though, because in the grand scheme it is amazing how much this is exactly something that we should care about." -- Cummings on compactness

> "If you haven't spent considerable time thinking about this, or if you do not yet yet understand it perfectly, go brew another pot and settle in. You'll thank me later." -- Cummings on convergence

**Progressive complexity:**
Start with the simplest version of an idea and add layers:

1. Start simple: "A sequence converges if its terms get close to some number."
2. Add precision: "...arbitrarily close..."
3. Add the tail condition: "...and stay close from some point onward..."
4. Full formalism: "For every epsilon > 0, there exists N such that for all n > N, |a_n - L| < epsilon."

Each step refines the previous one, so the reader builds understanding in layers rather than confronting the complete formalism all at once.

### The Intuition-Before-Formalism Checklist

Before writing any formal definition, ask:

1. Have I explained in plain English what this concept captures?
2. Have I given a visual or physical analogy?
3. Have I acknowledged any counterintuitive aspects?
4. Have I started from the simplest case and built up?
5. Will the reader be able to predict roughly what the formal definition says before they read it?

If the answer to question 5 is "yes," the intuition-building has succeeded.

---

## 4. Historical Storytelling Integration

### History Is Not a Sidebar

In long-form mathematical exposition, history is not decoration placed in a shaded box that the reader can skip. History IS the exposition. The human drama of mathematical discovery -- the false starts, the rivalries, the eureka moments -- gives mathematics a narrative arc that sustains the reader through difficult material.

### Templates for Weaving History In

**Template 1: The Origin Story**

> "The story of [concept] begins with [person] in [year/era], who was trying to [problem they faced]..."

Use this when introducing a major concept for the first time. The historical context explains *why* the concept was developed.

Example (Cummings on Pythagoras and irrationals):

> "Pythagoras' story is cloaked in legend but fortunately the legends are all highly amusing. Aristotle wrote that Pythagoras had a golden thigh, was born with a golden wreath upon his head, and that after a deadly snake bit him, he bit the snake back, which killed it..."

Then the mathematical content -- the irrationality of sqrt(2) -- emerges naturally from the Pythagorean crisis.

**Template 2: The Rivalry**

> "[Mathematician A] believed [position]. [Mathematician B] disagreed violently, calling it [colorful insult]..."

Mathematical disagreements reveal what is at stake in the ideas.

Example (Cummings on Cantor):

Poincare called set theory "a grave disease." Kronecker called Cantor a "corrupter of youth." Yet Hilbert declared, "No one shall expel us from the paradise that Cantor has created." The reader experiences the controversy and understands why the results matter.

**Template 3: The Eureka Moment**

> "[Mathematician] was [doing something ordinary] when they realized..."

Example (Cummings on Archimedes):

> "He reportedly would become so engrossed in his geometry that he would forget to eat or bathe -- and when he did bathe he was still focused enough on his work that after once solving a problem mid-bath... he sprang from his tub and ran down the street naked yelling 'Eureka!'"

This makes the mathematician (and the mathematics) memorable.

**Template 4: The Long Road**

> "For [decades/centuries], mathematicians struggled with [problem]. First [Person A] tried [approach]. Then [Person B] realized..."

Example (Cummings on the estimation of pi):

> "Archimedes himself moved from 6-gons to 12-gons... eventually as far as a 96-gon, which he used to prove 3 + 10/71 < pi < 3 + 10/70... He was bested 700 years later by Chinese geometer Zu Chongzhi who... with an astonishing 24,576-gon proved that 3.1415926 < pi < 3.1415927."

The progression over centuries gives the reader a sense of the difficulty and the ingenuity involved.

### When to Include History

**Include history when:**
- Introducing a major concept (convergence, continuity, cardinality, the integral)
- A theorem has a surprising or contested history
- The historical context illuminates WHY the definition takes its particular form
- The human story makes an abstract concept memorable
- A rivalry or controversy reveals what is at stake

**Skip history when:**
- Performing routine computations
- Proving technical lemmas
- The history would interrupt a chain of reasoning
- The concept is purely a stepping-stone to something more important
- No interesting historical narrative exists

### Anecdotes That Illuminate the Mathematics

The best mathematical anecdotes are not mere trivia. They illuminate the mathematics itself.

- **Hippasus thrown overboard**: The legend dramatizes how threatening irrational numbers were to the Pythagorean worldview. The violence of the reaction reveals the depth of the conceptual revolution. After proving sqrt(2) is irrational: "How does that taste, Pythagoreans? Bitter? Mmmmm."
- **Cantor's persecution**: The hostility Cantor faced shows that his ideas about infinity were genuinely revolutionary, not just technical.
- **Archimedes' bathtub**: The ecstasy of discovery humanizes the method of exhaustion and makes it feel like a living achievement.
- **Einstein and hyperbolic geometry**: "When someone asks you whether this crazy theoretical math is good for anything in the real world, remind them that although mathematicians developed their theories of hyperbolic geometry simply because they were curious and thought it was fun, decades later Albert Einstein later asserted in his theory of relativity that the fabric of spacetime more closely resembles hyperbolic space..."

Each anecdote serves a pedagogical purpose beyond entertainment.

---

## 5. Questions That Drive Investigation

### The Principle

Use questions to structure sections around intellectual curiosity. A well-placed question turns a lecture into an investigation. The reader becomes a co-explorer rather than a passive recipient.

### How Cummings Uses Questions

Cummings uses numbered Questions to create a sense of guided investigation.

**Continuity chapter (p. 172):**

> "Question 6.1. Does there exist a function which is continuous at one point but not continuous at another?"
> "Question 6.2. Do there exist functions which are continuous nowhere?"

These questions structure the entire chapter. Each theorem and example is motivated by the drive to answer one of these questions.

**Sequences of functions (p. 326):**

> "Question 9.5. If f_k -> f pointwise, and each f_k is continuous, must f also be continuous?"

This single question motivates the entire distinction between pointwise and uniform convergence. The answer is "no" for pointwise convergence, which creates the need for a stronger notion.

### The Question-Driven Investigation Template

```
1. QUESTION: Pose a precisely stated mathematical question.
   - Make it genuinely interesting.
   - The reader should feel that the answer is not obvious.

2. EXPLORATION: Investigate through examples.
   - Try specific cases.
   - Look for patterns.
   - Build partial understanding.

3. PARTIAL ANSWER: Arrive at a partial or conditional result.
   - "If [extra condition], then yes."
   - Or: "Here's one example where it works, but..."

4. BETTER QUESTION: Refine the original question based on what we've learned.
   - "Under what conditions does [property] hold?"
   - "Is [extra condition] necessary, or can we weaken it?"

5. FULL ANSWER: State and prove the complete result.
   - The theorem feels earned, not imposed.
```

### Types of Driving Questions

| Type | Example | What It Drives |
|------|---------|---------------|
| Existence | "Does there exist a function continuous everywhere but differentiable nowhere?" | Construction or proof of impossibility |
| Preservation | "If each f_k is continuous, must the limit f be continuous?" | Discovering the right convergence notion |
| Characterization | "Which subsets of R are compact?" | Heine-Borel theorem |
| Classification | "How many sizes of infinity are there?" | Cantor's theorem, continuum hypothesis |
| Optimization | "What is the smallest N that works for a given epsilon?" | Sharpening convergence estimates |
| Generalization | "Does this result extend to R^n?" | Motivating higher-dimensional analysis |

### Making Questions Effective

- **State them precisely.** Vague questions ("What can we say about continuity?") do not drive investigation. Precise questions ("Does continuity of each f_k imply continuity of the limit?") do.
- **Place them at the beginning of sections**, not buried in the middle. The question should frame everything that follows.
- **Return to them explicitly** when the answer is found. "We can now answer Question 6.2: yes, such functions exist, and the Dirichlet function is one."
- **Let unanswered questions accumulate.** Some questions posed in Chapter 2 might not be answered until Chapter 8. This creates narrative tension and forward momentum.

---

## 6. Progressive Disclosure

### The Core Idea

Do not attempt to explain everything about a concept the first time it appears. Introduce ideas at the level of detail appropriate to the current context, and promise (and deliver) more depth later.

### Forward References

Use forward references to create narrative threads that span chapters.

> "We will come back to this problem in Chapter 4 (which is a chapter on series... hint hint)." -- Cummings, on Zeno's paradox

> "It will take over a hundred pages of this text before we fully understand why Zeno was mistaken, but we'll get there." -- Cummings, p. 13

> "Exercise 2.12 highlights an important property of what are called open sets, which we will discuss in much greater detail in Chapter 5." -- Cummings, p. 69

> "Related ideas will return importantly in the area of real analysis called measure theory. If you get a PhD in math there's a good chance that measure theory will be the first topic you'll cover in your graduate real analysis class." -- Cummings, p. 69

Forward references serve several purposes:
- They assure the reader that loose ends will be tied up.
- They create anticipation and narrative momentum.
- They show the reader the larger structure of the subject.
- They give permission to move on without full understanding ("we'll come back to this").

### Incrementally Building Morals

After each result, state a "Moral" -- a plain-English lesson. Make each successive moral slightly more surprising than the last.

Cummings' cardinality morals (Ch. 2):

1. "The Moral. Two sets can have the same size even though one is a proper subset of the other." (after showing |N| = |{2,3,4,...}|)

2. "The Moral. Two sets can have the same size even though one is a proper subset of the other and the larger one even has infinitely many more elements than the smaller one." (after showing |N| = |2N|)

3. "The Moral. Even though there are infinitely many rational numbers between every two consecutive integers, the two sets still have the same size." (after showing |Z| = |Q|)

4. "The Moral. There are different sizes of infinity, and |N|, |Z| and |Q| are all a smaller infinity than |R|." (after Cantor's diagonal argument)

Each moral builds on the previous one, raising the stakes. By the fourth moral, the reader's intuition has been thoroughly and delightfully demolished.

### Investigation Tables

Create tables with unknown entries ("???") that are filled in progressively through the chapter.

Cummings' pointwise vs. uniform convergence chart (p. 331) introduces a table early in the chapter with many "???" entries. As theorems are proved, entries are filled in one by one. This creates:

- A visual record of progress
- An ongoing sense of investigation
- A clear structure that the reader can refer back to
- Satisfaction as each entry is resolved

Template:

```
| Property              | Pointwise convergence | Uniform convergence |
|-----------------------|----------------------|---------------------|
| Preserves continuity? | ???                  | ???                 |
| Preserves integrals?  | ???                  | ???                 |
| Preserves derivatives?| ???                  | ???                 |
```

Then, after each theorem: "We can now fill in another entry in our table..."

### Notable Exercises

At the end of each chapter, highlight which exercises are particularly important and explain WHY, without doing the work for the reader.

> "Exercise 2.22 points out that most numbers we encounter in our lives -- or which come to mind when try to think about a random number -- are ridiculously well-behaved. As far as the real numbers go, conditions like rational and algebraic are the rarest of exceptions, rather than the rule." -- Cummings, p. 69

This guides the reader's effort without spoiling the discovery.

### The Progressive Disclosure Checklist

When introducing a concept:

1. Is this the first time the reader encounters this idea? If so, give only what they need now.
2. Will this concept appear again in a more advanced context? If so, say "we'll revisit this."
3. Can I state a simpler version now and the full version later?
4. Are there tangential details that would distract from the main thread? If so, save them for a reference or a later section.

---

## 7. Mathematical Writing Quality

This section is a complete reference for the writing rules that govern mathematical exposition, drawn primarily from Chartrand's Chapter 0.

### 7.1 Symbol Usage Rules

**Rule 1: Never start a sentence with a symbol.**

Every sentence begins with a word, capitalized. If a symbolic expression must lead, introduce it with a word.

| Bad | Good |
|-----|------|
| x^2 - 6x + 8 = 0 has two distinct roots. | The equation x^2 - 6x + 8 = 0 has two distinct roots. |
| n is an odd integer. | The integer n is odd. |
| f(x) = x^2 is continuous. | The function f(x) = x^2 is continuous. |

**Rule 2: Separate consecutive symbols with words.**

When two symbolic expressions appear next to each other, insert clarifying words between them.

| Bad | Good |
|-----|------|
| With the exception of a, b is the only root. | With the exception of a, the number b is the only root. |
| Consider S, T are subsets of R. | Consider sets S and T, which are subsets of R. |

**Rule 3: Use words instead of logical symbols in finished writing.**

The symbols =>, <=>, forall, exists, "s.t.", and similar abbreviations are for scratch work, not for finished exposition.

| Bad | Good |
|-----|------|
| forall epsilon > 0, exists N s.t. ... | For every epsilon > 0, there exists N such that... |
| P => Q | If P, then Q. |

**Rule 4: Be careful with "i.e." and "e.g."**

Near mathematical symbols, these abbreviations can create visual clutter. When in doubt, write "that is" and "for example" instead.

**Rule 5: Write out small integers used as adjectives.**

| Context | Convention |
|---------|-----------|
| Adjective use | "There are exactly two groups of order four." |
| Mathematical value | "For n = 2, we get..." |

**Rule 6: Do not mix words and symbols improperly.**

| Bad | Good |
|-----|------|
| Every integer >= 2 is prime or composite. | Every integer that is at least 2 is prime or composite. |
| Since (x-2)(x-3) = 0, then x = 2 or 3. | Since (x-2)(x-3) = 0, it follows that x = 2 or x = 3. |

**Rule 7: Do not use a symbol exactly once in a theorem statement.**

If a symbol appears in a theorem only to be immediately discarded, omit it.

| Bad | Good |
|-----|------|
| Every bijective function f has an inverse. | Every bijective function has an inverse. |

**Rule 8: Explain every new symbol when introduced.**

> "If you write n = 2k + 1 and k has never appeared before, then say that k is an integer (if indeed k is an integer)."

Every variable must be introduced with its type immediately upon first use.

**Rule 9: Use frozen symbols conventionally.**

Certain symbols carry conventional meaning. Respect these conventions.

| Convention | Symbols |
|-----------|---------|
| Integers | m, n, k, j |
| Real numbers | x, y, z, t |
| Functions | f, g, h |
| Sets | A, B, C, S, T |
| Small positive numbers | epsilon, delta |
| Limits / bounds | L, M, N |

Do not use n for a real number or epsilon for an integer.

**Rule 10: Use consistent symbol families.**

When introducing paired or grouped variables, use symbols from the same family.

| Bad | Good |
|-----|------|
| x = 2a and y = 2r | x = 2a and y = 2b |
| Let m and r be integers. | Let m and n be integers. |

### 7.2 Word and Phrase Guidelines

**Use "we" as the default pronoun.**

> "It is not considered good practice to use 'I' unless you are writing a personal account. Using 'one' is often awkward. Using 'we' is standard practice in mathematics." -- Chartrand

**"Since" vs. "If":**

- "Since" introduces a fact that has been established: "Since n is odd, we have n = 2k + 1."
- "If" introduces a hypothesis or condition: "If n is odd, then n^2 is odd."

Never use "Since...then" -- this is a grammatical error.

| Bad | Good |
|-----|------|
| Since n^2 is even, then n is even. | Since n^2 is even, it follows that n is even. |
| Since n^2 is even, then n is even. | If n^2 is even, then n is even. |

**"Any" vs. "Each" vs. "Every":**

The word "any" is ambiguous (it can mean "every" or "some" depending on context). Replace it with a precise alternative.

| Bad | Good |
|-----|------|
| For any integer n... | For every integer n... |
| If any element satisfies... | If some element satisfies... |

**"That" vs. "Which":**

- "That" introduces a restrictive clause (essential to meaning, no comma): "The set that contains all primes..."
- "Which" introduces a nonrestrictive clause (parenthetical, with comma): "The set S, which is finite, has..."

**Vary transitional words.**

Do not use "Therefore" at the start of every concluding sentence. Alternatives: thus, hence, consequently, so, it follows that, this implies that, we conclude that, this gives.

### 7.3 Equation Formatting

**Inline vs. display:**
- Short expressions go inline: "Since n = 2k + 1, we have..."
- Long or important expressions get a centered display.

**Alignment:**
In multi-step computations, align equal signs vertically:

```
n^3 + 3n^2 - n + 4 = (2k+1)^3 + 3(2k+1)^2 - (2k+1) + 4
                    = 8k^3 + 24k^2 + 16k + 7
                    = 2(4k^3 + 12k^2 + 8k + 3) + 1.
```

**Line-breaking:**
When an expression must break across lines, end the first line with the operator or comparison symbol (+, -, =, <, >=). Never start a new line with these symbols.

| Bad | Good |
|-----|------|
| a^4 + 4a^3b \n + 6a^2b^2 | a^4 + 4a^3b + \n 6a^2b^2 |

**Every equation is part of a sentence.**

Display equations should be punctuated (comma, period, semicolon) and integrated into the surrounding text.

### 7.4 Common Conventions and Misspellings

**Do not hyphenate "non-" prefixes in mathematics:**

| Wrong | Right |
|-------|-------|
| non-empty | nonempty |
| non-negative | nonnegative |
| non-decreasing | nondecreasing |
| non-zero | nonzero |

**Commonly misspelled mathematical words:**

commutative, complement, consistent, feasible, occurrence, parallel, preceding, principle (not principal), proceed, corollary, lemma, theorem

**Conventional verb pairings:**

| We... | ...a/an |
|-------|---------|
| ask | questions |
| pose | problems |
| present | solutions |
| prove | theorems |
| solve | problems |
| state | definitions |
| verify | conjectures |

---

## 8. Tone and Voice

### Conversational but Rigorous

The ideal tone for long-form mathematics combines casual, engaging phrasing with uncompromising mathematical precision. The informality lives in the framing, the transitions, the asides. The rigor lives in the definitions, the proofs, the logical structure.

This is not "dumbing down." It is making the mathematics *more* accessible without making it *less* correct.

### Direct Address Patterns

Speak to the reader directly. Use "you" and "we." Ask them to think.

**Invitation to think:**
> "So, what do you think? Does slow and steady win the race?"

**Encouragement to persist:**
> "If you haven't spent considerable time thinking about this, or if you do not yet understand it perfectly, go brew another pot and settle in. You'll thank me later."

**Acknowledgment of difficulty:**
> "Bear with me, though, because in the grand scheme it is amazing how much this is exactly something that we should care about."

**Celebration of results:**
> "Make sure you take a moment to appreciate how remarkably, wonderfully weird this is."

**Reassurance:**
> "This is kind of a bummer. We might have hoped that pointwise convergence would preserve the continuity property, but sadly it is not strong enough."

### Humor Patterns

Humor in mathematical writing serves a pedagogical purpose: it keeps the reader engaged through difficult material, makes concepts memorable, and humanizes the subject.

**Footnote asides:**
Footnotes are the primary vehicle for humor. They allow jokes and tangential remarks without interrupting the mathematical flow.

> "(Fun fact: '0' was first discovered by an ancient Babylonian who asked how many of his friends wanted to talk about numbers with him.)"

> "He loved kids, but because they are small, he called them 'epsilons.'" (on Paul Erdos)

> "Sometimes two wrongs do make a right! Take that, Mom!" (on double negation in absolute value)

**Running gags:**
> "Make sure you take a moment to appreciate how wonderfully weird this is." -- This phrase recurs across multiple chapters as a running footnote gag, appearing each time a result defies intuition.

**Historical humor:**
> "How does that taste, Pythagoreans? Bitter? Mmmmm." (after proving sqrt(2) irrational)

**Self-aware absurdity:**
> "oo bottles of beer on the wall, oo bottles of beer. Take one down, pass it around, oo bottles of beer on the wall." (on infinite cardinality)

**Mathematical wit:**
> "So 2 < 1? Preposterous! We have our contradiction."

**Guidelines for humor:**
- Never let a joke obscure the mathematics.
- Footnotes and asides are the safest location for humor.
- Self-deprecating or self-aware humor works well.
- Humor about the mathematics itself (surprising results, strange definitions) lands better than unrelated jokes.
- A single well-placed joke per section is usually enough.

### Enthusiasm

Express genuine excitement about mathematical results. If the writer is not excited, the reader will not be either.

> "Make sure you take a moment to appreciate how remarkably, wonderfully weird this is."

> "Beautifully, there is a single elegant axiom that we can include to capture all of these properties..."

> "Math's pretty neat." (after showing the area under x^2 is exactly 1/3)

> "So get ready, because I think you will enjoy it."

Enthusiasm should feel authentic. It works best at genuinely surprising or beautiful results, not at routine computations.

### Encouragement

Acknowledge when material is difficult. Never pretend that hard things are easy. Instead, motivate persistence.

> "Fair warning: The proof is quite long and arduous. But... surprisingly when I surveyed my last real analysis class on what their favorite theorem was throughout the course, quite a few said the Heine-Borel theorem, and they specifically cited the toughness of the proof as a reason!"

> "You'll thank me later."

> "Go brew another pot and settle in."

The message is: "This is hard, and that's okay, and you can do it, and it will be worth it."

### Avoiding Condescension

**Never use "clearly," "obviously," "of course," or "certainly" as a substitute for reasoning.**

> "These and similar words can turn a reader off if what's written is not clear to the reader. It can give the impression that the author is putting the reader down. These words should be used sparingly and with caution." -- Chartrand

If something is truly immediate, you do not need to say "clearly" -- just state it. If it requires thought, saying "clearly" is a lie that makes the reader feel inadequate.

| Bad | Good |
|-----|------|
| Clearly, f is continuous. | Since f is a polynomial, it is continuous. |
| Obviously, this set is open. | Every point of this set has an epsilon-neighborhood contained in it, so it is open. |
| It is trivial to verify that... | One can verify that... (and then verify it) |

---

## 9. Anti-Patterns in Mathematical Exposition

These are the most common failures in mathematical writing. Recognizing them is as important as knowing the positive patterns.

### 9.1 Starting with Bare Formal Definitions

**The problem:** Presenting a definition with no motivation, no intuition, no examples.

**What it looks like:**
> "Definition 3.1. A sequence (a_n) in R converges to L in R if for every epsilon > 0, there exists N in the natural numbers such that for all n > N, |a_n - L| < epsilon."
> "Theorem 3.2. If (a_n) converges to L, then (a_n) is bounded."
> "Proof. ..."

**What is missing:** Why do we care about convergence? What does it mean intuitively? What are examples? What are non-examples?

**The fix:** Follow the five-step Definition Introduction Workflow (Section 2).

### 9.2 "The Proof Is Left as an Exercise to the Reader"

**The problem:** Using this phrase to abdicate responsibility for explaining something the reader needs to understand.

**When it is acceptable:** For results that are genuinely routine applications of techniques the reader has already mastered, AND where the exercise of proving it is itself valuable.

**When it is not acceptable:** For results that are surprising, difficult, or foundational. If the reader needs the result to understand what follows, prove it.

**Better alternatives:**
- Provide a proof sketch: "The key idea is... The details are similar to Theorem 3.4."
- Give a hint: "Try using the triangle inequality with epsilon/2."
- Prove it in full and then offer a generalization as an exercise.

### 9.3 Dry, Impersonal Tone

**The problem:** Writing that treats mathematics as a sequence of definitions and theorems with no human element.

**What it looks like:**
> "We now state the following result."
> "The proof proceeds as follows."
> "We have the following theorem."

**The fix:** Use the tone patterns from Section 8. Ask questions. Express enthusiasm. Acknowledge difficulty. Speak to the reader as a person.

### 9.4 Excessive Abstraction Without Concrete Examples

**The problem:** Defining concepts in full generality without grounding them in specific instances.

**What it looks like:**
> "Let X be a topological space, and let {U_alpha} be an open cover. We say X is compact if every open cover has a finite subcover."

(With no examples of what X, the U_alpha, or the finite subcover look like in practice.)

**The fix:** After every abstract definition, give at least two concrete examples and one non-example. Show what the definition looks like "on the ground."

### 9.5 Skipping Non-Examples

**The problem:** Providing only positive examples of a definition. The reader knows what the concept IS but not what it is NOT. They cannot draw the boundary.

**What it looks like:**
> "Examples of fields include Q, R, and C."

**What is missing:** Why is Z not a field? Why is N not a field? Which specific axiom fails in each case?

**The fix:** For every definition, include at least one non-example with an explicit explanation of which condition fails and why. The non-examples often teach more than the examples.

### 9.6 Bare Equation Chains

**The problem:** Presenting a sequence of equations with no explanatory text.

**What it looks like:**
```
x + (-x) = x + x'
-x + (x + (-x)) = -x + (x + x')
(-x + x) + (-x) = (-x + x) + x'
0 + (-x) = 0 + x'
-x = x'
```

**What is good:**
```
Since x + (-x) = 0 = x + x', it follows, by adding -x to the equal
elements, that -x + (x + (-x)) = -x + (x + x'). By associativity,
(-x + x) + (-x) = (-x + x) + x'. Hence 0 + (-x) = 0 + x', and
therefore -x = x'.
```

**The rule:** Every equation chain must be accompanied by words explaining WHY each step is taken. "Since...it follows that," "By [theorem/definition]," "Therefore."

### 9.7 Using "Clearly" to Skip Reasoning

**The problem:** Using words like "clearly," "obviously," or "it is easy to see" to skip steps that are not easy for the reader.

**The damage:** The reader who does not see it "clearly" concludes they are stupid rather than that the author is lazy. This is the fastest way to lose a reader's trust and confidence.

**The rule:** If it is truly immediate, just state it without the qualifier. If it requires thought, provide the thought.

### 9.8 The "Wall of Abstraction" Opening

**The problem:** Beginning a chapter or section with a tower of definitions, one after another, before the reader has any idea why these concepts matter.

**What it looks like:**
> "Definition 1.1. A metric space is..."
> "Definition 1.2. An open ball is..."
> "Definition 1.3. An open set is..."
> "Definition 1.4. A closed set is..."
> "Definition 1.5. A limit point is..."

**The fix:** Introduce each definition when the reader needs it, motivated by a question or example. Interleave definitions with examples, motivation, and discussion. The reader should never encounter more than one or two definitions without a reason to care about them.

### Summary of Anti-Patterns

| Anti-Pattern | Core Issue | Fix |
|-------------|-----------|-----|
| Bare definitions | No motivation | Five-step workflow |
| "Left as exercise" | Abdicating responsibility | Prove it or give a real hint |
| Dry tone | No human element | Direct address, enthusiasm, humor |
| Pure abstraction | No grounding | Concrete examples after every definition |
| No non-examples | Incomplete understanding | Show what fails and why |
| Bare equations | No explanation | Words between every step |
| "Clearly" / "Obviously" | Skipping reasoning | State it or prove it |
| Wall of definitions | No pacing | Interleave with motivation and examples |
