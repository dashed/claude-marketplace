# Worked example, condensed

A billing feature on two stacked branches in a large Django monorepo (2026-09). Four test files
drove four production modules: a pure resolver test (module-level pytest functions), a DB read
test (three tests through the service layer), a DB parity test comparing a legacy read against a
platform read for every package, and a DB routing test through the routing backend.

Baseline: 61 tests, 757 code lines, 1106 total lines. Identifiers are omitted; the shapes are
what transfer.

## What the oracles said

**Fact matrix.** Seven strict subsets; twenty-one single-pinned facts; one fact pinned only at
the wrong layer (a pure-function property pinned only through a DB test). One layer down, a
package parity test already pinned by exact list comparison every "package X publishes value Y"
assertion the resolver tests repeated.

**Coverage.** Six of 61 tests had a non-empty unique set. An 11-test covering set reproduced the
514-item baseline exactly when run alone. The other 50 tests were coverage-redundant — and most
of them survived anyway, on assertion strength.

**Comment audit.** Fourteen blocks; eighteen lines of prose removable; two false statements,
including a module comment claiming the expected value was never written into the file, above
five hard-coded copies of it.

**Helper economics.** 141 of the 757 code lines were helpers and all but three cleared their cost. 35 of
the 44 recoverable lines were width overflow — one-expression calls wrapped to three lines by
long method and enum names.

## What was done

- **The DB read test file was deleted.** Every fact in it was already proved by the parity sweep,
  the package parity test one layer down, or the routing suite. Its two unique facts moved: "an
  override stays on its own category" into the pure resolver test, "no record resolves to None"
  into the parity file as a two-line test.
- **Resolver test, 27 → 20.** Three strict subsets deleted; four tests of one function folded
  into one; two scalar tests folded into one that also pins the relocated fact — proven by a
  mutant that derived the scalars from the lifted per-category mapping and failed the sharpened
  test. The first draft of that assertion used a fixture where the lift was invisible (a
  thirteen-month exemption kept the value equal); the mutant run is what exposed it.
- **Routing test, 24 → 18.** Four tests that each built the same annual fixture to pin one
  eligibility fact became one test under a distinct-value patch, which made every assertion
  stronger; two error-origin tests share a body; two unmigrated-state tests share a body; a test
  whose three facts three other tests carried was deleted; two read aliases and three enum
  aliases collapsed the width-wrapped calls.
- **Parity file.** Comments trimmed per block; a literal 90 replaced by the production constant
  it was; the provisioning instant named.

## What was refused, on the reports' own advice

- Parametrizing the resolver's eight eligibility tests: line-neutral after the shortening
  devices, minus eight descriptive names.
- A shared record builder in the test utilities: three lines net, and the first of its kind
  against fifteen local helpers.
- Merging two parity divergence tests: it would have collapsed two resolver branches into one
  row label.

## Process defects found on the way

- An unquoted `$files` in zsh is not word-split; the linter received one bogus path and passed
  having checked nothing, and three over-width lines reached a pushed tip. Lint with explicit
  paths; read `git diff --stat` afterwards.
- The first mutant fixture was invisible to the mutant (an exemption kept the value equal). A
  relocated fact is proven only when the mutant run fails.

## Result

| | before | after |
|---|---:|---:|
| tests | 61 | 46 |
| code lines | 757 | 608 |
| total lines | 1106 | 896 |
| branch coverage, four production modules | baseline | identical per module |
