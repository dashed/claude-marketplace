# Conventional Commits 1.0.0 - Full Specification

Source: https://www.conventionalcommits.org/en/v1.0.0/

## Summary

The Conventional Commits specification is a lightweight convention on top of commit messages. It provides an easy set of rules for creating an explicit commit history; which makes it easier to write automated tools on top of. This convention dovetails with [SemVer](http://semver.org), by describing the features, fixes, and breaking changes made in commit messages.

## Message Structure

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Structural Elements

1. **fix:** a commit of the _type_ `fix` patches a bug in your codebase (correlates with `PATCH` in Semantic Versioning).

2. **feat:** a commit of the _type_ `feat` introduces a new feature to the codebase (correlates with `MINOR` in Semantic Versioning).

3. **BREAKING CHANGE:** a commit that has a footer `BREAKING CHANGE:`, or appends a `!` after the type/scope, introduces a breaking API change (correlates with `MAJOR` in Semantic Versioning). A BREAKING CHANGE can be part of commits of any _type_.

4. **Other types:** `build:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, and others are allowed.

5. **Footers** other than `BREAKING CHANGE: <description>` may be provided and follow git trailer format.

A scope may be provided after a type for additional context: `feat(parser): add ability to parse arrays`.

## Examples

### Commit message with description and breaking change footer
```
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files
```

### Commit message with `!` to draw attention to breaking change
```
feat!: send an email to the customer when a product is shipped
```

### Commit message with scope and `!` to draw attention to breaking change
```
feat(api)!: send an email to the customer when a product is shipped
```

### Commit message with both `!` and BREAKING CHANGE footer
```
chore!: drop support for Node 6

BREAKING CHANGE: use JavaScript features not available in Node 6.
```

### Commit message with no body
```
docs: correct spelling of CHANGELOG
```

### Commit message with scope
```
feat(lang): add Polish language
```

### Commit message with multi-paragraph body and multiple footers
```
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Remove timeouts which were used to mitigate the racing issue but are
obsolete now.

Reviewed-by: Z
Refs: #123
```

## Specification Rules

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" are interpreted as described in RFC 2119.

1. Commits MUST be prefixed with a type, which consists of a noun (`feat`, `fix`, etc.), followed by the OPTIONAL scope, OPTIONAL `!`, and REQUIRED terminal colon and space.

2. The type `feat` MUST be used when a commit adds a new feature to your application or library.

3. The type `fix` MUST be used when a commit represents a bug fix for your application.

4. A scope MAY be provided after a type. A scope MUST consist of a noun describing a section of the codebase surrounded by parenthesis, e.g., `fix(parser):`

5. A description MUST immediately follow the colon and space after the type/scope prefix. The description is a short summary of the code changes, e.g., _fix: array parsing issue when multiple spaces were contained in string_.

6. A longer commit body MAY be provided after the short description, providing additional contextual information about the code changes. The body MUST begin one blank line after the description.

7. A commit body is free-form and MAY consist of any number of newline separated paragraphs.

8. One or more footers MAY be provided one blank line after the body. Each footer MUST consist of a word token, followed by either a `:<space>` or `<space>#` separator, followed by a string value.

9. A footer's token MUST use `-` in place of whitespace characters, e.g., `Acked-by`. An exception is made for `BREAKING CHANGE`, which MAY also be used as a token.

10. A footer's value MAY contain spaces and newlines, and parsing MUST terminate when the next valid footer token/separator pair is observed.

11. Breaking changes MUST be indicated in the type/scope prefix of a commit, or as an entry in the footer.

12. If included as a footer, a breaking change MUST consist of the uppercase text BREAKING CHANGE, followed by a colon, space, and description.

13. If included in the type/scope prefix, breaking changes MUST be indicated by a `!` immediately before the `:`. If `!` is used, `BREAKING CHANGE:` MAY be omitted from the footer section.

14. Types other than `feat` and `fix` MAY be used in your commit messages.

15. The units of information that make up Conventional Commits MUST NOT be treated as case sensitive by implementors, with the exception of BREAKING CHANGE which MUST be uppercase.

16. BREAKING-CHANGE MUST be synonymous with BREAKING CHANGE when used as a token in a footer.

## SemVer Relationship

| Commit Type | SemVer Impact |
|-------------|---------------|
| `fix` | PATCH release |
| `feat` | MINOR release |
| Any type with `BREAKING CHANGE` | MAJOR release |

## FAQ

### How should I deal with commit messages in the initial development phase?

Proceed as if you've already released the product. Typically *somebody*, even if it's your fellow software developers, is using your software. They'll want to know what's fixed, what breaks etc.

### Are the types in the commit title uppercase or lowercase?

Any casing may be used, but it's best to be consistent. Lowercase is conventional.

### What do I do if the commit conforms to more than one of the commit types?

Go back and make multiple commits whenever possible. Part of the benefit of Conventional Commits is its ability to drive us to make more organized commits and PRs.

### What do I do if I accidentally use the wrong commit type?

**Wrong type of the spec (e.g., `fix` instead of `feat`):** Use `git rebase -i` to edit the commit history before merging or releasing.

**Type not of the spec (e.g., `feet` instead of `feat`):** The commit will be missed by tools based on the spec, but it's not the end of the world.

### Do all my contributors need to use the Conventional Commits specification?

No! If you use a squash based workflow, lead maintainers can clean up the commit messages as they're merged.

### How does Conventional Commits handle revert commits?

Use the `revert` type with a footer referencing the commit SHAs being reverted:

```
revert: let us never again speak of the noodle incident

Refs: 676104e, a215868
```
