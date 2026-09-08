# Layering review

Open this file when the path census in [between-function-complexity.md](between-function-complexity.md)
has said what it can say — a path is two to four times its baseline in hops, decisions, or threaded
names — and the question left is which layers stay. The numbers locate; this file judges. It is to
the path census what [interpreting-scores.md](interpreting-scores.md) is to the per-function census.

**Provenance.** The worked example throughout is one real case: a value-returning read with three
public shapes (a per-key value, a second per-key value, and the whole mapping) switched from a
legacy computation to a platform service in a large Django monorepo, reviewed on two unmerged
branches against their base. Its census numbers were measured with the skill's commands and the
scripts in `scripts/` — 23 defs / Σ cognitive 61 / 34 decisions on the new path against 7 / 24 / 9
on the path it replaced; 35 callables entered per public call against 11. Its hop, site, and test
counts were made by hand and then reproduced by the scripts within the tolerances stated in
between-function-complexity.md. The simplification it recommends was implemented afterwards: the
suite stayed green, and every assertion that changed was a tag or a set, never a served value.
Identifiers are omitted; the shapes are what transfer. Where a claim is inference rather than
observation it is labelled **(inferred)**.

## Table of contents

- [Structure or safety](#structure-or-safety)
- [Write the invariants once](#write-the-invariants-once)
- [Compare against siblings](#compare-against-siblings)
- [What the tests pin](#what-the-tests-pin)
- [Alternatives and the before/after table](#alternatives-and-the-beforeafter-table)
- [Order the work](#order-the-work)
- [Policy questions are not layering questions](#policy-questions-are-not-layering-questions)
- [Reporting shape](#reporting-shape)
- [Unverified](#unverified)

## Structure or safety

The test is one sentence per layer: *without this, X happens.* If X is a wrong answer served, an
exception reaching a caller that cannot contain it, a forbidden import, or a stale value, the layer
is **safety** and it stays — the only question is its form. If X is "the code would be arranged
differently", the layer is **structure**. Structure is what makes a path hard to follow, and it is
what the path census counts: hops, threaded names, intermediate types, decisions that re-derive
something a caller already knew.

Five structural costs recur. Each is a shape, a symptom a reader feels, the count that measures it,
and the fix that usually applies.

**(a) A selector threaded through signatures and compared late.** A string or enum chosen at the
public entry ("which of my three reads is this?") is passed down every signature and compared, in
several functions near the bottom, to re-discover what the top already knew. The reader holds
"which read am I in?" for the whole descent because the code answers it late and in several
places. This is Ousterhout's *pass-through variable* and Fowler's *flag argument*; adding a fourth
read shape would touch every site (*Shotgun Surgery*). Measure: `arg_threading.py --name <selector>`
— signatures carrying it, compare sites, and distinct functions that compare. In the example: 8
signatures, compared at 8 sites across 4 functions, 38 sites in all, plus 2 `@overload` stubs
narrowing it. Fix: *Remove Flag Argument* — one typed public function per shape, sharing one
private router. The selector survives only as a metric label nothing branches on.

**(b) A fact decided in one layer, applied in another, threaded back to pick a tag.** A rule's
result (a set of keys the rule lifts) is computed by the producer, applied by the consumer, and the
fact that it was applied travels back up through a field on an intermediate type, an `any()`, and
`tuple[value, bool]` returns on three functions — so that the top can choose one telemetry tag
string. Nothing served depends on the bool. This is *information leakage*: one decision reflected
in several modules. Measure: for every returned field, name its consumer; a field with exactly one
consumer that is a metric call is this shape. The representations recipe counts the carriers;
`hops.py` shows the distance between where the fact is decided and where it is applied. Fix: apply
the rule where it is decided; emit the metric at that moment. In the example, two sets, two fields
on a NamedTuple, an `any()` over twenty booleans, and three tuple-returning functions existed to
choose one tag.

**(c) N fallback helpers with N semantics.** Three functions each produce "the default answer" —
for no contract, for an empty resolution, for a missing key — and their values differ in every
non-trivial cell. Executing the producer against hand-built inputs shows two of them are
value-identical for every input it can generate; the third differs in one cell nobody can trigger.
It reads as drift, not design. This is the escalation Metz describes in *The Wrong Abstraction*
(essay): an abstraction that was almost right grows a parameter and a conditional per new case.
Measure: list every site that produces the same default constant; execute the producer's empty
and missing cases by hand and compare. Fix: one named source of the default, kept as the only
fallback; keep the distinct metric tags, which tell an operator a data fault from an outage.

**(d) Representation churn.** K intermediate types stand between the input record and the wire
shape; the same conversion runs twice over the same keys; a whole mapping is rebuilt to answer a
single-key read; nothing is memoised between three reads of the same input per request. Fowler's
*Message Chains* and *Middle Man*; Ousterhout's *shallow module* (an interface complicated relative
to what it hides). Measure: the representations recipe (package-defined types constructed on the
path, plus tuple-returning callables); `hops_dyn.py` invocation counts higher than the number of
keys expose rebuild-to-read-one directly. In the example: 5 intermediate types, the conversion run
twice, a ten-key map rebuilt to read one. Fix: the producer returns the wire shape with the read
methods on it; a single-key read becomes a field lookup; the duplicate projection is deleted.

**(e) A module split forced by an import lint.** Two modules exist because one of them must import
a model that a lint forbids under the other's tree, and the gate is called as a method on that
model. The boundary is real; the extra module is a choice — a sibling switch in the same codebase
used the id-based function form of the same gate and needed no split. Measure: `by module` in
`hops.py`, then for each module ask why it exists; the answer "because file X may not import Y"
names a boundary, not a layer. The sibling table below shows whether others pay the same split.
Fix: switch to the form of the gate that is legal on the inner side, and fold; or keep the file and
say so. Either is defensible; the current state is the more expensive one to read.

Two of Fowler's names are worth keeping to hand. *Lazy Element* — "a function that's named the same
as its body code reads" — is the diagnosis for a glue hop, and its fix is *Inline Function*.
*Speculative Generality* is (b) seen from the other side: machinery built for a distinction nothing
served needs. Folklore has labels too ("ravioli code", "death by a thousand indirections"); use
them as labels, never as sources.

Ousterhout's reading test is free: if you find yourself flipping back and forth between two
functions to understand either, that is a red flag — and *"You shouldn't break up a method unless it
makes the overall system simpler."* On the example's path, every function is well named and every
function is read alongside its neighbour.

## Write the invariants once

Walk the path and list candidates: every `try/except`, gate, fallback, cache, lazily-passed
callable, and lint-driven boundary. For each, answer *what breaks without it, for whom.* Keep the
ones with an answer; state them once, numbered, so every alternative can be checked against the
same list.

The example's list, in shapes:

- **I1** The routed arm reads no legacy model beyond the migration flag and an id; the legacy
  computation is passed as a callable that is never invoked for a migrated tenant.
- **I2** No platform exception reaches the caller (which batches many tenants per request — one
  raising tenant would fail the batch); a failure serves a stated default and emits one metric per
  outcome.
- **I3** Parity with the legacy computation, including each of its special cases, enumerated.
- **I4** The read shapes and their edge semantics, one line each: what a missing key serves, what an
  absent tier serves, what the whole-mapping read contains.
- **I5** A second consumer of the pure producer keeps working.
- **I6** The import boundary the lint enforces.

Then the table. One row per layer or construct, the invariant it protects (or "none"), and a
verdict from a fixed vocabulary: **keep** · **keep the invariant, change the form** · **collapse**
(several functions become fewer) · **fold** (a module joins another) · **delete**.

| Layer / construct | Invariant it protects | Verdict |
| --- | --- | --- |
| Gate on the migration flag, legacy computation as a lazy callable | I1 | **Keep the invariant.** The callable is the cheapest statement of it; whether it needs its own module is (e) |
| `try/except` → stated default, never legacy | I2 | **Keep one.** Two handlers for one policy, converging on the same default, is structure |
| Distinct metric tag per degradation | I2, operability | **Keep** |
| The one named source of the default value | I2 | **Keep**, and make it the only fallback (fold the other two into it) |
| Pure, typed producer under the boundary | I3, I5, I6 | **Keep.** Pre-dates the change; has a second consumer |
| Sets / booleans / `(value, bool)` returns that pick a tag | none — only the tag | **Delete**, or one metric call where the fact is decided |
| Producer's output type (a tuple of input-shaped records) | none — the next layer converts it at once | **Change** to the wire shape, so the whole-mapping read is a field |
| The selector string | none — re-encodes which public function was called | **Delete.** Three typed functions carry it in their names |
| Five shape-conversion functions in the serve layer | I4 | **Collapse** to three ~5-line functions once the producer returns the wire shape |
| The separate routing module | I6 | **Fold** by switching gate form, or keep and accept the file |

"Structure, not safety" in the verdict column is the whole review in three words. The rows marked
*keep* are the ones a simplification must not touch; everything else is on the table.

## Compare against siblings

Absolute counts mean little; the example's 23-vs-7 meant something because it was a ratio to the
path it replaced. The second baseline is the codebase's other switches of the same kind. Survey every
one and put them on one template:

| Switch | Gate | Modules between caller and service | On platform error | Parity compare | Rollout control |
| --- | --- | ---: | --- | --- | --- |
| a quota read | flag passed as a `bool` | 1 (inline) | falls back to legacy, even when platform is authoritative | every call | none |
| a seat read | percentage option + allowlist, then flag by id | 1 | falls back to legacy, with a comment saying it must | every call | percentage + allowlist |
| five API write sites | flag, sometimes behind a feature flag | 1 | authoritative side's own error; shadow failure swallowed | status only | feature flag on 2 sites |
| two serializers | flag | 1 | returns `None` ("cannot answer"); no `except` | none | none |
| a budget read | flag inline | 0 | falls back to legacy | none | none |
| **this read** | flag (method form) | **2** + the producer | **stated default, never legacy**; two `except` handlers | **none** | **none** |

The example's verdict on this table: *consistent in gate, telemetry and result shaping; an outlier
in two policies, not in layer count.* Two extra modules and two extra functions per call — and one
of the modules pre-dated the change and already had another consumer.

That reframes the review. The layer count was the weakest of the three criticisms. The two
outliers were policies — the failure path serves a computed default instead of legacy, and there is
no production parity compare — both deliberate, both documented in an earlier design note, and
each needing a reviewer's decision rather than a refactor. Without the sibling table the review
argues about layers and misses the policy. No written rule covered any of it; the policy lived in
code comments on two of the siblings. Record where the rule should live.

## What the tests pin

Read every test and classify it: **behaviour** (asserts a served number or mapping), **plumbing**
(asserts a metric tag, a set, a tuple ordering, a mock call, or a field of an intermediate type),
**mixed** (both in one test). Report per file:

| File | B | P | M | Total |
| --- | ---: | ---: | ---: | ---: |
| routing suite | 3 | 0 | 25 | 28 |
| producer suite | 12 | 12 | 3 | 27 |
| read-shape suite | 0 | 1 | 2 | 3 |
| parity suite | 3 | 0 | 4 | 7 |

The routing suite was almost all behaviour with a route-tag assertion bolted on; the plumbing
concentrated in the producer suite, where 12 of 27 tests asserted only the sets or the tuple order.

**The boundary is refactor-relative.** A test that asserts a served value *through a shape the
refactor deletes* — a helper that reads the producer's tuple, a duplicate projection in the parity
suite — is plumbing for that refactor and behaviour for every other. So do not classify in the
abstract; name the refactor first. Two readers will move a few tests between columns; that is
expected.

**The mechanical check that is reliable** is *tests broken as written by refactor X*: write X's
deletion set (the names, fields, tags, and shapes it removes) as a regex and scan every test body
plus the same-file helpers the test calls — a test that *builds* the old shape breaks as surely as
one that asserts on it, and an asserts-only scan misses it. The recipe is in
between-function-complexity.md. For the example:

| Refactor | routing | producer | read-shape | parity | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| R1 rule applied inside the producer; sets, booleans and the tag removed | 8 | 10 | 0 | 2 | **20** — every one a tag or set assertion, no served value |
| R2 producer returns the wire shape | 1 | 11 | 2 | 7 | **21** — mechanical, through three near-identical test helpers |
| R3 selector → typed functions; fallbacks merged | 1–3 | 0 | 0 | 0 | **1–3** |
| R4 router folded | 0–1 | 0 | 0 | 0 | **0–1** |

That table is the cost column of the alternatives matrix. The scripts reproduced R1 and R2 exactly
from the deletion sets.

Ask next: **if every plumbing test were deleted, which served values lose their only coverage?** In
the example, two — both edge cases of one eligibility rule; everything else had a served-value
twin in another suite. Those two get a behaviour test before anything moves.

Then: **behaviours with no test at all**, which a refactor could change in silence. Branch coverage
does not find these; they are intersections. The example had four: one read shape combined with
one override kind (each tested alone, never together); a zero reaching the wire through one path
while another path floored it; an unmapped key landing on a wrong key without an error; and the
one below.

**The coincident-constants trap, as a rule.** Before moving a rule between layers, add a fixture
whose value is distinct from every default it could be confused with. In the example the rule's
lifted value, the stack default, and one package's default were all 90, so a rule applied twice —
once in the producer where it moved to, once in the consumer where it was forgotten — lifted 90 to
90 and passed the whole suite. A fixture at 75 made a double application fail. Add it first, as its
own commit.

One more shape: a test that guards less than its name says. The example had a test named for the
equality of two constants that deleted the input which would have exercised the rule, making it a
subset of another test. If the intent is the equality, the honest form is a one-line assertion
importing both constants.

## Alternatives and the before/after table

Work each candidate shape against the invariant list and put them on one matrix:

| | Shape | Deletes | Tests broken as written | Loses | Risk |
| --- | --- | --- | --- | --- | --- |
| **A** | Status quo | — | — | — | The open review thread stays open; the selector grows a branch per shape; two fallbacks diverge on a case nobody can trigger; a projection written twice disagrees on an edge |
| **B** | Rule applied where it is decided | the sets, the carrier type, the `(value, bool)` channel, the tag | 20, all tag/set | per-read observability of the rule (one metric call at the decision replaces it) | ordering inside the producer is subtle when the rule reads a package default while other keys keep resolved values; B wants C's single pass |
| **C** | Producer returns the wire shape with read methods | the rebuild-to-read-one function, the second conversion pass, a `cast`, the parity suite's duplicate projection | 21, mechanical | nothing | one extra dataclass |
| **D** | Typed entry points + one private router; serve module deleted | the selector type, both overloads, the serve module's five functions, two of three fallbacks | 1–3 | the distinct values of one fallback — unreachable in production | the router is generic over the value type |
| **E** | Name the platform helpers like the legacy ones so both arms read alike | — | — | — | standalone it adds indirection; it falls out of C + D for free |

Then the before/after columns, measured or counted on the sketches:

| Measure | Before | After (B + C + D) | Δ |
| --- | ---: | ---: | ---: |
| Hops per public call, branch-owned | 21 | 17 | −4 |
| …of which glue between the caller and the producer | 10 | 4 | **−6** |
| Modules beyond the caller | 3 | 2 | −1 |
| Defs + classes | 30 | 26 | −4 |
| `@overload` stubs | 2 | 0 | −2 |
| Functions that branch on the selector | 4 | 0 | **−4** |
| Intermediate representations | 5 | 2 | −3 |
| Lines | 647 | ~470 | ~−180 |

Read the table honestly. The definition count barely moves, and that is the true result: 11 of the
21 hops were small pure helpers, each stating one precedence rule, and they were never the problem.
What leaves is the glue, the selector, the carriers, the duplicated projection, and the
two-flavour fallback. Say which served values change — in the example, two, both toward safety (a
zero scalar is floored everywhere instead of on one path; the empty-resolution path serves the
stated default it already effectively served) — and pin each with a test.

One layer that looked like structure survived the matrix: the router itself. The flag read can
raise, and the design says neither arm is then trusted; a bare `bool` cannot express that, and
inlining the guard into the caller copies it once per read shape. So a routing module still earns
its place — at about 55 lines instead of roughly 300 across two files **(inferred from the
sketches; not measured after the change)**.

## Order the work

Rank the steps by independence and by what each unblocks, and say which one to take if only one is
taken. In the example: **B first** — it answers the open review thread, removes the carriers and
the channel, and depends on nothing. **C second** — it deletes a projection written twice and
inconsistently. **D last** — its value is mostly realised once C has made the read shapes
one-liners.

If the branches are unmerged, change the branches rather than land-then-refactor: small PRs, each
with a green suite, the first cut off the base branch so it pays for itself alone. The prerequisite
fixture (the distinct value from the coincident-constants rule) goes in before any of them.
Orthogonal improvements — a short-TTL cache around the producer was one — must not gate the
layering change; list them, mark them optional.

## Policy questions are not layering questions

Some of what reads as complexity is a policy, and refactoring it away decides the policy by
accident. Separate these out and hand them to the reviewer as questions with the trade-off stated.
The example's four, generalised:

1. **Fallback target on infrastructure failure.** A computed default (legacy-free; matches a
   documented rule; but degrades every migrated tenant at once, and a degraded cached answer can
   outlive the outage) versus legacy (what every sibling does; correct data during an outage; but
   reinstates a legacy dependency on the routed arm) versus a middle position (legacy only when
   the flag read itself fails, since that tenant may well be unmigrated).
2. **Does a telemetry tag earn its plumbing?** If a counter of occurrences is enough, a third of a
   layer goes.
3. **Is a shadow or parity phase needed?** Every sibling value-returning switch compared both
   arms on every call before its flag flipped; this one had parity tests and no production
   compare, so the first signal of a divergence would be customer-visible.
4. **Is an asymmetry between fallbacks intentional?** If not, one helper replaces three; if so, it
   needs a comment and a test.

Each is a decision, not a shape. The review's job is to make the trade-off legible, not to pick.

## Reporting shape

BLUF first: the verdict in two words ("partly justified"); what stays and the invariant each
protects; what is structure; the numbers (path census and hops, against both baselines); the
sibling verdict; the recommendation with its before/after; the one-thing-if-only-one; the
prerequisite fixture. Then the sections above in order.

Every load-bearing claim carries a `path:line@ref` cite, where `@ref` names the checkout — the
routing tip, the read tip, the base — because the same function has different line numbers on each.
Close with an **Unverified** section: what was not executed (hop counts and shape counts read from
source are by hand until a script reproduces them); which checkouts were read and whether they
match the base the change targets; which counts rest on an assumption (a per-key multiplier
derived from an inheritance chain by hand); what a tool could not resolve. A reader who wants to
re-derive a number should be able to find its command or its caveat.

## Unverified

- The worked example is one case. The five structural costs are the five it exhibited, not a
  taxonomy; a different switch will show others.
- The sibling-table columns come from one codebase's switches; another codebase's template will
  differ.
- The behaviour/plumbing/mixed counts are one reader's. The scripts reproduced the routing suite
  exactly and moved a few tests in the other three suites; the *breakage* counts (R1 = 20,
  R2 = 21) are the reproducible part.
- The recommended shape was implemented on the branches with a green suite; whether it merged in
  that form, and the post-change line counts (~470, ~55), were not checked here.
- Hops "before" (21) required hand-written exclusion of three functions reachable only on untaken
  branches; the unpruned static count is 24. See between-function-complexity.md for the
  definition used.
