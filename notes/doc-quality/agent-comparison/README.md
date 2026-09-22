# Blind reviewer comparison

The [parent report](../README.md#blind-comparison) records the protocol and limits.
`baseline.json` was frozen before Jev results; `assisted.json` was frozen before
expected labels were disclosed. `comparison.json` stores input hashes and every
scored observation. Both reviews match 30/30 labels, with no changed decisions.

To recompute, load `tests/fixtures/doc-quality.json`, index both review files by
case `name`, and iterate each case's `expectations`. The expected value is `equals`
for `preferred`; `minimum` is a true Boolean label and `maximum` is false for
preservation judgments. Compare that value with each review's field of the same
signal name. Score only the 30 frozen assertions. Null is an abstention and never
correct. Keep decision changes separate from improvements and regressions.
