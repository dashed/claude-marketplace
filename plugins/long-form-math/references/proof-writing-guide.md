# Proof Writing Guide

A comprehensive reference for writing proofs in the long-form mathematics style. Covers the three-phase proof pattern, templates for every major proof technique, in-line commentary, the almost-correct proof pattern, common mistakes, and a technique selection flowchart.

---

## Table of Contents

1. [The Three-Phase Proof Pattern](#1-the-three-phase-proof-pattern)
2. [Proof Templates by Technique](#2-proof-templates-by-technique)
3. [In-Line Commentary Patterns](#3-in-line-commentary-patterns)
4. [The Almost-Correct Proof Pattern](#4-the-almost-correct-proof-pattern)
5. [Common Proof Mistakes](#5-common-proof-mistakes)
6. [Technique Selection Flowchart](#6-technique-selection-flowchart)

---

## 1. The Three-Phase Proof Pattern

Every nontrivial proof should follow a three-phase structure: **Strategy**, **Proof**, and **Analysis**. This pattern makes the invisible thinking process visible and gives the reader understanding, not just verification.

### Phase 1: Pre-Proof Strategy

Before the formal proof, show the reader how the proof was discovered. This is labeled **Scratch Work** (Cummings) or **Proof Strategy** (Chartrand).

**What to include:**

- **Goal identification.** State clearly what must be shown. Write the conclusion you need to reach.
- **Working backward.** Start from the desired conclusion and manipulate it toward known facts or assumptions.
- **Technique selection.** Explain why you are choosing a particular proof method (direct, contradiction, etc.). If a direct approach runs into trouble, say so explicitly.
- **Handling difficulties.** If the path is not straightforward, show where the obstacles are and how you navigate them.
- **The key insight.** If the proof depends on a clever trick (adding and subtracting a term, choosing a specific epsilon, partitioning into cases), reveal it here with motivation.

**For long proofs, also provide a Proof Idea:** A plain-English summary of the high-level strategy, in one or two sentences, so the reader has a map before entering the technical details.

### Full Example: The Three-Phase Pattern in Action

**Theorem.** If $(a_n)$ is a sequence of real numbers such that $a_n \to a$ and $a_n \to b$, then $a = b$.

**Proof Idea.** We show that $|a - b|$ is smaller than every positive number, which forces $|a - b| = 0$. The triangle inequality provides the key bridge between the two convergence assumptions.

**Scratch Work.** We want to show $a = b$, or equivalently $|a - b| = 0$. A natural approach is to show $|a - b| < \varepsilon$ for every $\varepsilon > 0$, since the only nonnegative number less than every positive number is zero.

Given $\varepsilon > 0$, we know:
- Since $a_n \to a$, there exists $N_1$ such that $n > N_1$ implies $|a_n - a| < \varepsilon/2$.
- Since $a_n \to b$, there exists $N_2$ such that $n > N_2$ implies $|a_n - b| < \varepsilon/2$.

If we take $N = \max(N_1, N_2)$ and pick any $n > N$, the triangle inequality gives:

$$|a - b| = |a - a_n + a_n - b| \leq |a_n - a| + |a_n - b| < \varepsilon/2 + \varepsilon/2 = \varepsilon.$$

That works. The key trick is splitting $\varepsilon$ into two halves — one for each convergence assumption.

**Proof.** Let $\varepsilon > 0$. Since $a_n \to a$, there exists a positive integer $N_1$ such that $|a_n - a| < \varepsilon/2$ for every $n > N_1$. Since $a_n \to b$, there exists a positive integer $N_2$ such that $|a_n - b| < \varepsilon/2$ for every $n > N_2$.

Let $N = \max(N_1, N_2)$ and let $n > N$. By the triangle inequality,

$$|a - b| = |(a - a_n) + (a_n - b)| \leq |a_n - a| + |a_n - b| < \frac{\varepsilon}{2} + \frac{\varepsilon}{2} = \varepsilon.$$

Since $|a - b| < \varepsilon$ for every $\varepsilon > 0$, and $|a - b| \geq 0$, we conclude that $|a - b| = 0$, and therefore $a = b$. $\square$

**Moral.** This proof illustrates a fundamental technique in analysis: to show two quantities are equal, show their difference is smaller than every positive number. The triangle inequality is the workhorse that connects separate estimates into a single bound.

**Alternative approach.** The result can also be proved by choosing $\varepsilon = (b - a)/3$ (assuming $a < b$) and showing that the $\varepsilon$-neighborhoods of $a$ and $b$ are disjoint, creating a contradiction when $a_n$ must eventually lie in both. This geometric argument is more visual but slightly longer.

### Phase 2: The Proof Itself

The proof is the polished, forward-directed argument. It should read like a finished narrative, not scratch work.

**Template structure:**

```
Proof.
  [1] State what is assumed. ("Let n be an odd integer.")
  [2] Unpack definitions. ("Then n = 2k + 1 for some integer k.")
  [3] Perform computation, with each step justified.
      ("Therefore, n^2 = (2k+1)^2 = 4k^2 + 4k + 1 = 2(2k^2 + 2k) + 1.")
  [4] Identify the key expression. ("Since 2k^2 + 2k is an integer, ...")
  [5] Conclude by stating what has been shown.
      ("...we conclude that n^2 is odd.")
```

**Rules for the proof body:**

- State assumptions first, before doing anything else.
- Introduce every new variable with its type: "where $k$ is an integer", not just "$n = 2k + 1$".
- At each step, explain **why** it is taken, not just what happens.
- Use words between equations (see Section 3).
- Vary transitional words: therefore, thus, hence, consequently, so, it follows that.
- Conclude by explicitly restating what has been proved.

### Phase 3: Post-Proof Analysis

After the proof, step back and reflect. This is labeled **Proof Analysis** (Chartrand) or **Moral** (Cummings).

**What to include:**

- **Could this be simpler?** Is there a shorter or more elegant route?
- **The moral.** What does this result teach us, in plain English? What is the conceptual takeaway?
- **Alternative proofs.** If a different technique would illuminate a different aspect, sketch it or point to it.
- **Reverse-engineering insight.** Show how the polished proof was constructed by working backward from the goal. This answers: "How would I ever think of this?"
- **Extensions and connections.** Does this result generalize? Does it connect to a bigger picture?

---

## 2. Proof Templates by Technique

### 2.1 Direct Proof

**When to use.** The hypothesis directly provides enough information to derive the conclusion. This is the default — try it first.

**Template:**

```
Proof. Assume that [hypothesis] holds for an arbitrary [element type].
Then [unpack the definition]: [variable] = [expression], where [variable] is [type].
Therefore, [computation with justification].
Since [key expression] is [type], we conclude that [conclusion]. ▢
```

**Example.** *The sum of two even integers is even.*

*Proof.* Let $m$ and $n$ be even integers. Then $m = 2a$ and $n = 2b$ for some integers $a$ and $b$. Therefore,

$$m + n = 2a + 2b = 2(a + b).$$

Since $a + b$ is an integer, we conclude that $m + n$ is even. $\square$

**Common mistake.** Writing $m = 2k$ and $n = 2k$. This forces $m = n$. Use distinct variables for independent quantities.

### 2.2 Proof by Contrapositive

**When to use.** The hypothesis gives a complicated expression that is hard to work with directly, but the negation of the conclusion gives a simpler starting point. If proving $P \Rightarrow Q$, instead prove $\lnot Q \Rightarrow \lnot P$.

**Decision heuristic.** If starting from the hypothesis leads to an expression like $(2a + 7)/5$ where you cannot tell whether it is even an integer, try the contrapositive — you may get a cleaner starting expression.

**Template:**

```
Proof. We prove the contrapositive: if [not Q], then [not P].
Assume that [not Q] for an arbitrary [element type].
Then [unpack negated conclusion], so [computation].
Therefore [negated hypothesis holds], which completes the proof. ▢
```

**Example.** *If $5x - 7$ is even, then $x$ is odd.*

*Scratch Work.* A direct proof would assume $5x - 7 = 2a$, giving $x = (2a + 7)/5$. It is not clear this is an integer, let alone odd. The contrapositive — assume $x$ is even — gives us $x = 2k$, which is much easier to work with.

*Proof.* We prove the contrapositive: if $x$ is even, then $5x - 7$ is odd. Assume that $x$ is even, so $x = 2k$ for some integer $k$. Then

$$5x - 7 = 5(2k) - 7 = 10k - 7 = 10k - 8 + 1 = 2(5k - 4) + 1.$$

Since $5k - 4$ is an integer, $5x - 7$ is odd. $\square$

### 2.3 Proof by Contradiction

**When to use.** The result is "negative-sounding" — it asserts that something does not exist, cannot happen, or is impossible. Also useful when neither direct proof nor contrapositive yields a clean path.

**Template:**

```
Proof. Assume, to the contrary, that [negation of statement].
Then [derive consequences from this assumption].
[Arrive at a statement that contradicts a known fact, an axiom, or the hypothesis.]
This is a contradiction. Therefore, [original statement] holds. ▢
```

**Example.** *There is no rational number whose square is 2.*

*Proof.* Assume, to the contrary, that there exists a rational number $r$ such that $r^2 = 2$. Write $r = p/q$ where $p$ and $q$ are integers with $q \neq 0$ and $\gcd(p, q) = 1$. Then $p^2 = 2q^2$, so $p^2$ is even. Since $p^2$ is even, $p$ itself is even (the square of an odd number is odd). Write $p = 2k$ for some integer $k$. Then $(2k)^2 = 2q^2$, which gives $4k^2 = 2q^2$, so $q^2 = 2k^2$. By the same reasoning, $q$ is even. But then both $p$ and $q$ are even, contradicting $\gcd(p, q) = 1$. $\square$

**Common mistake.** Arriving at a "contradiction" that is not actually contradictory — for example, deriving that a variable is both positive and nonnegative (which is consistent, not contradictory).

### 2.4 Proof by Cases

**When to use.** The domain partitions naturally into cases (even/odd, positive/negative/zero, $n \leq k$ vs. $n > k$), and no single argument handles all cases at once.

**Requirements:**
- Cases must be **exhaustive** (cover every possibility).
- Cases should be **disjoint** when possible (to avoid redundancy).

**Template:**

```
Proof. We consider [number] cases.

Case 1: [condition]. [Proof for this case.]

Case 2: [condition]. [Proof for this case.]

Since these cases are exhaustive, the result follows. ▢
```

**The WLOG pattern.** When two cases are symmetric (e.g., "either $a \leq b$ or $b \leq a$"), prove one and state: "Without loss of generality, assume $a \leq b$." But you **must** explain **why** there is no loss of generality — the cases must truly be interchangeable by symmetry.

**Example.** *For every integer $n$, the integer $n^2 + n$ is even.*

*Proof.* We consider two cases based on the parity of $n$.

**Case 1:** $n$ is even. Then $n = 2k$ for some integer $k$, so $n^2 + n = 4k^2 + 2k = 2(2k^2 + k)$, which is even.

**Case 2:** $n$ is odd. Then $n = 2k + 1$ for some integer $k$, so $n^2 + n = (2k+1)^2 + (2k+1) = 4k^2 + 4k + 1 + 2k + 1 = 4k^2 + 6k + 2 = 2(2k^2 + 3k + 1)$, which is even.

Since every integer is either even or odd, we conclude that $n^2 + n$ is even for every integer $n$. $\square$

### 2.5 Existence Proofs

#### Constructive Existence

**When to use.** The statement asserts "there exists an $x$ such that..." and you can explicitly exhibit such an $x$.

**Template:**

```
Proof. We claim that [explicit object] satisfies the required property.
Indeed, [verify the property by direct computation]. ▢
```

**Example.** *There exists an integer $n$ such that $n^3 = n$.*

*Proof.* We claim that $n = 1$ satisfies this property. Indeed, $1^3 = 1 = 1$. $\square$

#### Non-Constructive Existence

**When to use.** You can prove that an object must exist (via contradiction, the pigeonhole principle, or another theorem) without explicitly constructing it.

**Template:**

```
Proof. Assume, to the contrary, that no [object] satisfies [property].
[Derive a contradiction from this assumption.]
Therefore, such an [object] must exist. ▢
```

### 2.6 Uniqueness Proofs

**When to use.** The statement asserts that exactly one object has a certain property. Uniqueness proofs typically combine an existence proof with a uniqueness argument.

**Template for the uniqueness part:**

```
To show uniqueness, suppose that both x and x' satisfy [property].
Then [derive from the property that x and x' must be equal].
Therefore x = x'. ▢
```

**Example.** *The additive identity in a ring is unique.*

*Proof.* Let $0$ and $0'$ both be additive identities in a ring $R$. Since $0$ is an additive identity, $0 + 0' = 0'$. Since $0'$ is an additive identity, $0 + 0' = 0$. Therefore $0 = 0 + 0' = 0'$. $\square$

### 2.7 Mathematical Induction

**When to use.** The statement involves a natural number parameter and the truth of each case builds on the previous one. Typical pattern: the claim holds for all $n \geq n_0$ where $n_0$ is some base case.

**Template:**

```
Proof. We proceed by induction on n.

Base case (n = n_0): [Verify the statement directly for the smallest value.]

Inductive step: Assume that [statement holds for n = k] for some integer k >= n_0.
  We must show that [statement holds for n = k + 1].
  [Derive the k+1 case, using the inductive hypothesis explicitly.]

By the principle of mathematical induction, [statement] holds for all n >= n_0. ▢
```

**Example.** *For every positive integer $n$, we have $1 + 2 + \cdots + n = n(n+1)/2$.*

*Proof.* We proceed by induction on $n$.

**Base case** ($n = 1$): The left side is $1$. The right side is $1 \cdot 2 / 2 = 1$. The base case holds.

**Inductive step:** Assume that $1 + 2 + \cdots + k = k(k+1)/2$ for some positive integer $k$. We must show that $1 + 2 + \cdots + k + (k+1) = (k+1)(k+2)/2$. Starting from the left side and applying the inductive hypothesis:

$$1 + 2 + \cdots + k + (k+1) = \frac{k(k+1)}{2} + (k+1) = \frac{k(k+1) + 2(k+1)}{2} = \frac{(k+1)(k+2)}{2}.$$

This completes the inductive step. By the principle of mathematical induction, the formula holds for all positive integers $n$. $\square$

**Common mistake.** Using the inductive hypothesis without labeling it. Always write "by the inductive hypothesis" when you invoke the assumption for $n = k$.

### 2.8 Epsilon-Delta Proofs (The Two-Phase Pattern)

**When to use.** Proving that a limit exists, that a sequence converges, or that a function is continuous — any statement involving $\varepsilon$ and $\delta$ (or $\varepsilon$ and $N$).

**The two-phase approach (from Chartrand):**

**Phase 1 — Scratch Work (backward).** Work backward from the desired inequality.

1. Write out what needs to be shown: $|f(x) - L| < \varepsilon$.
2. Algebraically manipulate to isolate $|x - a|$ (or $1/n$ for sequences).
3. Impose a restriction on $\delta$ (typically $\delta \leq 1$) to bound other factors.
4. Compute the resulting bound $K$, so that $|f(x) - L| < K \cdot |x - a|$.
5. Set $\delta = \min(1, \varepsilon/K)$.

**Phase 2 — Proof (forward).** Present the argument cleanly from hypotheses to conclusion.

```
Proof. Let epsilon > 0 be given. Choose delta = min(1, epsilon/K).
Let x be a real number such that 0 < |x - a| < delta.
Since delta <= 1, [bound other factors using the restriction].
Since delta <= epsilon/K, [derive the final inequality].
Therefore |f(x) - L| < epsilon. ▢
```

**Example.** *Show that $\lim_{x \to 2}(x^2 + 1) = 5$.*

*Scratch Work.* We need $|x^2 + 1 - 5| < \varepsilon$, i.e., $|x^2 - 4| < \varepsilon$. Factor: $|x - 2| \cdot |x + 2| < \varepsilon$. We need to bound $|x + 2|$. If $\delta \leq 1$, then $|x - 2| < 1$, so $1 < x < 3$, which gives $3 < x + 2 < 5$. Hence $|x + 2| < 5$. We need $5|x - 2| < \varepsilon$, so $|x - 2| < \varepsilon/5$. Choose $\delta = \min(1, \varepsilon/5)$.

*Proof.* Let $\varepsilon > 0$ be given. Choose $\delta = \min(1, \varepsilon/5)$, and let $x$ be a real number such that $0 < |x - 2| < \delta$.

Since $\delta \leq 1$, we have $|x - 2| < 1$, so $1 < x < 3$, and therefore $|x + 2| < 5$.

Since $\delta \leq \varepsilon/5$, we have $|x - 2| < \varepsilon/5$. Therefore,

$$|x^2 + 1 - 5| = |x^2 - 4| = |x - 2| \cdot |x + 2| < \frac{\varepsilon}{5} \cdot 5 = \varepsilon.$$

This shows that $\lim_{x \to 2}(x^2 + 1) = 5$. $\square$

**The $\min$ pattern.** The choice $\delta = \min(1, \varepsilon/K)$ simultaneously ensures that the bounding argument works ($\delta \leq 1$) and that the final inequality is satisfied ($\delta \leq \varepsilon/K$). This is a signature move in epsilon-delta proofs.

---

## 3. In-Line Commentary Patterns

### The Principle

Every proof step should explain **why** it is taken, not just **what** happens. The reader should never face a chain of bare equations without accompanying words.

### Words Between Equations

**Bad (bare equation chain):**
```
x + (-x) = x + x'
-x + (x + (-x)) = -x + (x + x')
(-x + x) + (-x) = (-x + x) + x'
0 + (-x) = 0 + x'
-x = x'
```

**Good (with explanatory words):**

Since $x + (-x) = 0 = x + x'$, it follows, by adding $-x$ to both sides, that $-x + (x + (-x)) = -x + (x + x')$. By associativity, $(-x + x) + (-x) = (-x + x) + x'$. Hence $0 + (-x) = 0 + x'$, and therefore $-x = x'$.

### Connective Phrases

Use these phrases to link steps and explain reasoning:

**Causal connectives (explaining why):**
- "Since $n$ is even, we have $n = 2k$ for some integer $k$."
- "Because $f$ is continuous on $[a,b]$, the extreme value theorem guarantees..."
- "By the triangle inequality, $|x + y| \leq |x| + |y|$."
- "By hypothesis, $a_n \to a$."

**Consequential connectives (stating what follows):**
- "Therefore, $n^2$ is even."
- "Thus, $f(c) = 0$ for some $c \in (a,b)$."
- "Hence, the sequence converges."
- "Consequently, $|f(x) - L| < \varepsilon$."
- "So $p$ must be even."
- "It follows that $S$ is bounded."
- "This implies that $g$ is injective."

**IMPORTANT: Vary your transitions.** Do not write "Therefore" three times in a row. Rotate through the options above.

**Attribution phrases (citing a result):**
- "By Theorem 3.5, ..."
- "By the definition of convergence, ..."
- "Applying the Bolzano-Weierstrass theorem, ..."
- "By the inductive hypothesis, ..."

### The "Since/If" Distinction

This is a subtle but important rule:

- **"Since"** is for facts already established or assumed. "Since $n$ is odd" (we already know this).
- **"If"** is for hypothetical conditions. "If $n$ were even, then..."

**Wrong:** "If $n$ is odd" when $n$ was assumed odd in the hypothesis.
**Right:** "Since $n$ is odd" when $n$ was assumed odd in the hypothesis.

### Commentary at Key Steps

At critical junctures in a proof — the clever trick, the key substitution, the moment where the hypothesis is used — add a parenthetical or a sentence explaining the motivation:

- "We add and subtract $ab_n$ (a standard trick that separates the two limits)..."
- "This is where we use the completeness of the reals: the supremum exists because $S$ is bounded above."
- "Note that without the continuity assumption, this step fails (see Section 6.3)."

---

## 4. The Almost-Correct Proof Pattern

One of the most powerful pedagogical tools: show a proof attempt that **almost** works, diagnose exactly where and why it fails, then fix it. This builds the reader's ability to evaluate proofs critically.

### Structure

1. **State the theorem and a candidate proof attempt.**
2. **Present the attempt** as if it were correct, without flagging the error in advance.
3. **Pause and examine.** Ask: "Does this work?" or "Where does this argument break down?"
4. **Diagnose the failure.** Pinpoint the exact step where the reasoning is invalid and explain **why**.
5. **Fix the proof.** Either repair the flawed step or use a different technique entirely.
6. **State the moral.** What does the failure teach us about the concept?

### Example: Pointwise vs. Uniform Convergence

**Claim.** If $f_k \to f$ pointwise and each $f_k$ is continuous, then $f$ is continuous.

**Proof attempt.** Let $\varepsilon > 0$ and let $c$ be a point in the domain. Since $f_k \to f$ pointwise, there exists $N$ such that $|f_N(x) - f(x)| < \varepsilon/3$ for all $x$. Since $f_N$ is continuous at $c$, there exists $\delta > 0$ such that $|x - c| < \delta$ implies $|f_N(x) - f_N(c)| < \varepsilon/3$. Then by the triangle inequality...

**Wait.** Read the second sentence again. We wrote: "there exists $N$ such that $|f_N(x) - f(x)| < \varepsilon/3$ **for all $x$**." But pointwise convergence only guarantees that for **each fixed $x$**, there exists $N_x$ (depending on $x$) such that the approximation holds. The $N$ we need might be different for each point $x$.

**Diagnosis.** The proof attempt secretly used **uniform** convergence (a single $N$ works for all $x$ simultaneously) when only pointwise convergence was given. This is the crucial distinction:

- **Pointwise:** For each $x$, for each $\varepsilon > 0$, there exists $N_x$ such that...
- **Uniform:** For each $\varepsilon > 0$, there exists $N$ such that **for all $x$**...

The order of quantifiers matters. In pointwise convergence, $N$ depends on $x$. In uniform convergence, $N$ is independent of $x$.

**The fix.** The claim is actually **false** under pointwise convergence. A counterexample: let $f_k(x) = x^k$ on $[0,1]$. Each $f_k$ is continuous, and $f_k \to f$ pointwise where $f(x) = 0$ for $x \in [0,1)$ and $f(1) = 1$. The limit $f$ is discontinuous at $x = 1$.

The correct theorem requires **uniform** convergence: if $f_k \to f$ uniformly and each $f_k$ is continuous, then $f$ is continuous.

**Moral.** Pointwise convergence preserves almost nothing about the individual functions. Uniform convergence is the stronger condition needed to transfer properties like continuity from the approximating functions to the limit. Whenever you find yourself needing "the same $N$ for all $x$," you are implicitly invoking uniform convergence.

### When to Use This Pattern

- When a subtle hypothesis is easy to overlook (uniform vs. pointwise, open vs. closed, bounded vs. unbounded).
- When a common student mistake reveals a genuine conceptual distinction.
- When the failure is more instructive than a correct proof would be on its own.
- When the fix illuminates why a hypothesis exists in a theorem.

---

## 5. Common Proof Mistakes

### 5.1 Reusing Variables for Independent Quantities

**The mistake:** When two objects satisfy the same property, using the same variable for both.

**Bad:**
> Let $a$ and $b$ be even integers. Then $a = 2k$ and $b = 2k$ for some integer $k$.

This forces $a = b$, which was not assumed. The proof now only handles the case where both integers are equal.

**Good:**
> Let $a$ and $b$ be even integers. Then $a = 2k$ and $b = 2l$ for some integers $k$ and $l$.

**Rule.** Every existential unpacking introduces a **fresh** variable. If two objects independently satisfy a property, they get independent witnesses.

### 5.2 Proof by Example

**The mistake:** Verifying a universal claim for specific values and concluding it holds in general.

**Bad:**
> *Claim:* The sum of two odd integers is even.
> *"Proof":* $3 + 5 = 8$, which is even. $7 + 11 = 18$, which is even. Therefore the sum of two odd integers is even.

This proves nothing about, say, $13 + 29$, let alone all pairs. Examples can illustrate, motivate, and build intuition, but they cannot replace a general argument.

**When examples ARE proofs.** Existence proofs ("there exists an $n$ such that...") can be proved by a single example. Disproving universal claims ("not every $n$ satisfies...") requires only one counterexample.

### 5.3 Assuming What You Are Proving

**The mistake:** Using the conclusion as part of the argument for the conclusion.

**Bad (proving $\sqrt{2}$ is irrational):**
> Assume $\sqrt{2} = p/q$ in lowest terms. Then $p^2 = 2q^2$, so $p$ is even. Write $p = 2k$. Then $4k^2 = 2q^2$, so $q^2 = 2k^2$, so $q$ is even. Since both are even, $\sqrt{2}$ is irrational.

The last sentence is a non sequitur. The correct conclusion is: "Since both $p$ and $q$ are even, this contradicts our assumption that $\gcd(p, q) = 1$. Therefore no such rational number exists." The proof must explicitly close the loop of the contradiction.

**A subtler form:** In a proof that $A \Rightarrow B$, writing "$B$ is true" in the middle and then using $B$ to derive further consequences, rather than deriving $B$ from $A$.

### 5.4 Missing WLOG Justification

**The mistake:** Writing "Without loss of generality, assume $X$" without explaining why there is no loss of generality.

**Bad:**
> Without loss of generality, let $a \leq b \leq c$.

If the claim treats $a$, $b$, $c$ symmetrically (e.g., "the sum $a + b + c$ is even"), then WLOG is justified because relabeling does not change the sum. But if the claim is not symmetric in $a$, $b$, $c$, then this assumption **does** lose generality.

**Rule.** Every use of WLOG must be accompanied by a brief justification: "Without loss of generality, assume $a \leq b$ (since the roles of $a$ and $b$ are symmetric in the hypothesis and conclusion)."

### 5.5 Using "Clearly" or "Obviously" to Skip Steps

**The mistake:** Disguising missing reasoning behind authority words.

**Bad:**
> Clearly, $f$ is continuous on $[0,1]$, and obviously the maximum is attained.

**Good:**
> Since $f$ is a polynomial, it is continuous on $[0,1]$. By the extreme value theorem, $f$ attains its maximum on $[0,1]$.

**Rule.** If a claim is truly immediate (one mental step), you can omit the justification entirely. If it requires even a small argument, provide it. Never use "clearly" as a substitute for a proof step you do not want to write.

### 5.6 Bare Equation Chains Without Words

**The mistake:** Presenting a sequence of equations with no connective text.

**Bad:**
```
n^2 + n = n(n+1)
= n(n+1)/2 * 2
QED
```

**Good:**
> We factor $n^2 + n$ as $n(n+1)$. Since one of $n$ and $n + 1$ is even (consecutive integers have opposite parity), their product $n(n+1)$ is even.

**Rule.** Every equation should be part of a sentence. The reader should never have to guess **why** one line follows from the previous one.

### 5.7 Failing to Introduce Variable Types

**The mistake:** Writing $n = 2k + 1$ without saying what $k$ is.

**Bad:**
> Since $n$ is odd, $n = 2k + 1$.

**Good:**
> Since $n$ is odd, $n = 2k + 1$ for some integer $k$.

If $k$ has not appeared before, the reader does not know whether it is an integer, a real number, or something else. State the type.

### 5.8 Confusing the Direction of an Implication

**The mistake:** Proving $Q \Rightarrow P$ when the claim is $P \Rightarrow Q$ (the converse error).

This is especially common in biconditional proofs, where both directions must be proved separately. Always label which direction you are proving and verify you have not mixed them up.

---

## 6. Technique Selection Flowchart

When facing a statement to prove, use this decision tree to select a technique. Start at the top and follow the first matching branch.

```
START: What kind of statement are you proving?
│
├─ Is it "P if and only if Q"?
│  └─ YES → Prove both directions separately (P⇒Q and Q⇒P).
│           Each direction may use a different technique.
│
├─ Does it assert "there exists" something?
│  ├─ Can you exhibit an explicit object? → Constructive existence proof.
│  └─ Cannot construct? → Non-constructive (contradiction, pigeonhole, etc.).
│
├─ Does it assert uniqueness ("there exists exactly one")?
│  └─ YES → Existence proof + assume two exist, show they are equal.
│
├─ Does it have a natural number parameter (holds "for all n ≥ n₀")?
│  └─ YES → Try mathematical induction.
│
├─ Is the conclusion "negative-sounding"?
│  │  ("no such X exists", "it is impossible that", "X is irrational")
│  └─ YES → Proof by contradiction. Assume the negation and derive
│           a contradiction.
│
├─ Does the hypothesis give a complicated expression?
│  │  (e.g., "if 5x - 7 is even" gives x = (2a+7)/5)
│  └─ YES → Try proof by contrapositive. Starting from ¬Q may give
│           a simpler expression to work with.
│
├─ Does the domain partition naturally into cases?
│  │  (even/odd, positive/negative/zero, n < k vs. n ≥ k)
│  └─ YES → Proof by cases. Check that cases are exhaustive.
│           Use WLOG if cases are symmetric.
│
├─ Does it involve limits, continuity, or convergence?
│  └─ YES → Epsilon-delta (or epsilon-N) proof.
│           Use the two-phase pattern (scratch work backward,
│           proof forward).
│
└─ DEFAULT → Try a direct proof. Assume the hypothesis,
             unpack definitions, compute toward the conclusion.
```

### Worked Decision Examples

**Statement:** "If $n^2$ is even, then $n$ is even."

- Not biconditional. Not existence. Not induction. Not negative-sounding.
- The hypothesis gives $n^2 = 2k$, so $n = \sqrt{2k}$ — complicated.
- **Try contrapositive:** Assume $n$ is odd. Then $n = 2m + 1$, so $n^2 = 4m^2 + 4m + 1 = 2(2m^2 + 2m) + 1$, which is odd. Clean and direct.

**Statement:** "There is no largest prime number."

- Negative-sounding ("there is no").
- **Use contradiction:** Assume there are finitely many primes $p_1, \ldots, p_k$. Consider $N = p_1 p_2 \cdots p_k + 1$. Then $N$ is not divisible by any $p_i$, contradicting the assumption that every integer greater than 1 has a prime factor among $\{p_1, \ldots, p_k\}$.

**Statement:** "For all $n \geq 1$, $2^n > n$."

- Natural number parameter with a base case.
- **Use induction.** Base case: $2^1 = 2 > 1$. Inductive step: $2^{k+1} = 2 \cdot 2^k > 2k \geq k + 1$ for $k \geq 1$.

**Statement:** "$A \subseteq B$ if and only if $A \cap B = A$."

- Biconditional ("if and only if").
- **Prove both directions.** ($\Rightarrow$) Assume $A \subseteq B$ and show $A \cap B = A$ by double containment. ($\Leftarrow$) Assume $A \cap B = A$ and show $A \subseteq B$ directly.

**Statement:** "The sequence $a_n = 1/n$ converges to 0."

- Involves convergence.
- **Epsilon-N proof.** Scratch work: we need $|1/n - 0| < \varepsilon$, i.e., $n > 1/\varepsilon$. Choose $N$ to be any integer greater than $1/\varepsilon$ (the Archimedean property guarantees such $N$ exists). The proof follows immediately.

---

## Quick Reference: Proof Opening Lines

| Technique | Opening Line |
|---|---|
| Direct | "Let $n$ be an [type] satisfying [hypothesis]." |
| Contrapositive | "We prove the contrapositive. Assume that [not Q]." |
| Contradiction | "Assume, to the contrary, that [negation of claim]." |
| Cases | "We consider two cases." |
| Existence (constructive) | "We claim that [explicit object] satisfies the property." |
| Uniqueness | "Suppose that both $x$ and $x'$ satisfy [property]." |
| Induction | "We proceed by induction on $n$. Base case ($n = n_0$): ..." |
| Epsilon-delta | "Let $\varepsilon > 0$ be given. Choose $\delta = \min(1, \varepsilon/K)$." |

---

## Quick Reference: Post-Proof Closing Lines

| Situation | Closing Line |
|---|---|
| Direct / contrapositive | "Therefore [restate conclusion]. $\square$" |
| Contradiction | "This contradicts [specific fact]. Therefore [original claim]. $\square$" |
| Cases | "Since these cases are exhaustive, [conclusion]. $\square$" |
| Induction | "By the principle of mathematical induction, [claim] holds for all $n \geq n_0$. $\square$" |
| Epsilon-delta | "This shows that $\lim_{x \to a} f(x) = L$. $\square$" |
