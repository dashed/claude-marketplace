# The no-comments lint rule and its ratchet

A lint rule that bans every comment fails on day one, because the purge never removes all of them in one change. A ratchet solves that: it records how many banned comments each file has now, fails when a count goes up, and requires the baseline to go down when a count goes down. This file shows the two ways to run it.

## Contents

- [Option A: the bundled ratchet (any language)](#option-a-the-bundled-ratchet-any-language)
- [Option B: an ESLint rule with bulk suppressions (JS and TS)](#option-b-an-eslint-rule-with-bulk-suppressions-js-and-ts)
- [Python linters](#python-linters)
- [Loopholes and how to close them](#loopholes-and-how-to-close-them)

## Option A: the bundled ratchet (any language)

Copy `scripts/comments.py` into the repository, so CI does not depend on this skill being installed. It is one file with PEP 723 metadata: `uv run --script` installs its only dependency, pygments.

```bash
cp "<this skill's directory>/scripts/comments.py" tools/comments.py
uv run --no-config --script tools/comments.py ratchet init src tests --exclude 'src/generated/*'
git add tools/comments.py .comment-ratchet.json
```

### The config

`.comment-ratchet.json` sits at the repository root. All paths in it are relative to that root.

| Field | Meaning |
|---|---|
| `paths` | the directories and files in scope |
| `exclude` | fnmatch globs matched against the relative path; `*` also matches `/` |
| `ban` | the banned kinds: `["plain"]`, or `["plain", "doc"]` to ban doc comments too |
| `allow` | extra regular expressions; a comment that matches one counts as a directive |
| `languages` | pygments language names to check, such as `["Python", "TypeScript"]`; empty means all |
| `message` | the text printed on failure; point it at the ADR that records the ban |
| `files` | the baseline: the banned comments allowed per file |

### Daily use

| Situation | Command |
|---|---|
| CI, on every change | `ratchet check --base origin/main` (needs the base branch fetched) |
| pre-commit, on staged files | `ratchet update FILE …`: lowers the counts of those files, fails on new comments |
| after deleting comments by hand | `ratchet update`, and commit the lower baseline in the same change |
| a reviewed exception | `ratchet update --allow-increase`; the higher count shows in the diff |
| a merge conflict in the baseline | take either side, then run `ratchet update` |

Run the whole-repository check in CI. Only it sees a baseline entry for a file that was deleted outside the hook, or excluded.

### When a count goes down

By default, `ratchet check` also fails when a file has *fewer* comments than the baseline records, until the lower count is committed. ESLint's bulk suppressions (exit status 2 on unused suppressions) and Betterer's CI mode (any difference from the results file) work the same way. Without it, the baseline is a cap, not a ratchet: a file that lost three comments can gain three new ones later, and the check passes.

The cost lands on a teammate who deletes a comment: the check fails and names a command they have not run before. The pre-commit hook below removes that cost. It runs `ratchet update` on the staged files, so it lowers the counts itself and fails only on a new comment. Like a formatter hook, it leaves the changed `.comment-ratchet.json` for the teammate to stage.

Renames do not fail the check: when git reports a renamed file, its count moves to the new path. A deleted file leaves the baseline at the next `ratchet update`.

To accept a cap instead, run the CI check with `--allow-stale`, and decide that on purpose: then only `ratchet update` lowers the baseline.

### pre-commit

```yaml
repos:
  - repo: local
    hooks:
      - id: comment-ratchet
        name: no new code comments
        entry: uv run --no-config --script tools/comments.py ratchet update
        language: system
        pass_filenames: true
```

A hook that edits a file fails the commit once, and pre-commit names the file; stage `.comment-ratchet.json` and commit again. Without uv, use `language: python`, `additional_dependencies: [pygments]`, and `entry: python tools/comments.py ratchet update`.

### GitHub Actions

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 0
- uses: astral-sh/setup-uv@v10
- run: uv run --no-config --script tools/comments.py ratchet check --base "origin/${{ github.base_ref || 'main' }}"
```

`fetch-depth: 0` gives `--base` a branch to diff against, so the failure marks the new comments with `(new)`. Without history the check still works; it only loses the marks.

### make

```make
lint-comments: ## Fail on new code comments
	uv run --no-config --script tools/comments.py ratchet check
```

Add the target to the repository's main lint or CI target.

### Protect the baseline

Add `.comment-ratchet.json` to `CODEOWNERS`, so that a raised count needs an owner's review.

## Option B: an ESLint rule with bulk suppressions (JS and TS)

ESLint 9.24 and later keep a ratchet natively: bulk suppressions record the current violations per file and rule in `eslint-suppressions.json`. A local rule bans the comments. Tested on ESLint 10.15.

`eslint-rules/no-comments.js`:

```js
const DIRECTIVES = [
  /^\s*eslint(-disable(-next-line|-line)?|-enable|-env)?(\s|$)/,
  /^\s*(globals?|exported)\s/,
  /^\s*@ts-(ignore|expect-error|nocheck|check)\b/,
  /^\s*prettier-ignore\b/,
  /^\s*(istanbul|c8|v8)\s+ignore\b/,
  /^\s*@jsx(ImportSource|Runtime|Frag)?\b/,
  /^\s*[@#]__(PURE|NO_SIDE_EFFECTS)__\s*$/,
  /^\/\s*<(reference|amd-module|amd-dependency)\b/,
  /^[!*]?\s*@(license|preserve)\b/,
  /^\s*[#@]\s*source(Mapping)?URL=/,
  /^\s*webpack[A-Z]\w*\s*:/,
  /^\s*@vite-ignore\b/,
];

export default {
  meta: {
    type: "suggestion",
    docs: { description: "Ban code comments, except tool directives" },
    schema: [
      {
        type: "object",
        properties: {
          allow: { type: "array", items: { type: "string" } },
          allowDocComments: { type: "boolean" },
        },
        additionalProperties: false,
      },
    ],
    messages: {
      banned: "Code comments are banned. Express the fact in code, a test, or an ADR.",
    },
  },
  create(context) {
    const options = context.options[0] ?? {};
    const allowed = [...DIRECTIVES, ...(options.allow ?? []).map((source) => new RegExp(source))];
    return {
      Program() {
        for (const comment of context.sourceCode.getAllComments()) {
          if (comment.type === "Shebang") continue;
          if (options.allowDocComments && comment.type === "Block" && comment.value.startsWith("*")) continue;
          if (allowed.some((pattern) => pattern.test(comment.value))) continue;
          context.report({ loc: comment.loc, messageId: "banned" });
        }
      },
    };
  },
};
```

`comment.value` excludes the `//` or `/* */` markers, which is why the triple-slash pattern starts at the third `/`.

`eslint.config.js`:

```js
import eslintComments from "@eslint-community/eslint-plugin-eslint-comments/configs";
import noComments from "./eslint-rules/no-comments.js";

export default [
  // ...the existing config
  {
    files: ["**/*.{js,jsx,ts,tsx,mjs,cjs}"],
    plugins: { local: { rules: { "no-comments": noComments } } },
    rules: { "local/no-comments": ["error", { allowDocComments: true }] },
  },
  eslintComments.recommended,
  {
    rules: {
      "@eslint-community/eslint-comments/no-restricted-disable": ["error", "local/no-comments"],
    },
  },
];
```

Seed the baseline for this rule only, so the suppressions file does not also hide the repository's other lint debt:

```bash
npx eslint --suppress-rule local/no-comments .
git add eslint-suppressions.json
```

From then on:

- A new comment fails `eslint`, which lists every comment in that file because the file's count went over.
- A removed comment makes `eslint` exit with status 2 and the message "There are suppressions left that do not occur anymore", until `npx eslint --prune-suppressions` lowers the count. `--pass-on-unpruned-suppressions` turns that failure off; leave it on, so the baseline stays tight.

The ESLint rule covers JS and TS only. For the rest of the repository, run the bundled ratchet with the JS and TS files left out, through `exclude` or `languages`.

## Python linters

Ruff has no rule that bans every comment, and no baseline file (a long-standing feature request, astral-sh/ruff#1149). Use the bundled ratchet for Python. Two Ruff rule families can add editor feedback on top of it, once the purge has removed what they flag:

- `ERA001` flags commented-out code (a stale comment).
- `FIX001`–`FIX004` flag `FIXME`, `TODO`, `XXX`, and `HACK` (excuses); the `TD` rules require an author and an issue link on a `TODO`.

Do not use `ruff check --add-noqa` to baseline them: it adds a `# noqa` comment to every violation, which is the opposite of this purge.

## Loopholes and how to close them

| Loophole | Close it |
|---|---|
| Prose attached to a directive: `# noqa: E501  # because …` | The ratchet allows it. `inventory` marks it `"prose": true`; review those items in Phase 2 and in code review. |
| An `eslint-disable` comment that disables the no-comments rule | `@eslint-community/eslint-comments/no-restricted-disable` with `local/no-comments`, as in the config above |
| Prose moved into a string, an unused constant, or a log message | Code review. The ratchet cannot see it; it is a comment in disguise. |
| A raised baseline | `CODEOWNERS` on `.comment-ratchet.json` or `eslint-suppressions.json` |
| A new directive pattern that the scanner does not know | Add it to `allow`, with a narrow regular expression, in a reviewed change |
