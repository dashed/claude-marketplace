---
name: skill-reviewer
description: Review and ensure skills maintain high quality standards. Use when creating new skills, updating existing skills, or auditing skill quality. Checks for progressive disclosure, mental model shift, appropriate scope, and documentation clarity.
---

# Skill Reviewer

Ensure skills maintain high quality standards through systematic review.

## When to Use

Use this skill when:
- Creating a new skill (before finalization)
- Updating an existing skill (after making changes)
- Auditing skill quality across your marketplace
- Reviewing team members' skill contributions

## Quick Review Process

### 1. Load the Skill

Read the skill's SKILL.md and check the directory structure:
```bash
ls -la path/to/skill/
cat path/to/skill/SKILL.md
```

### 2. Apply the 10-Point Checklist

Review against these core quality criteria:

1. **Progressive Disclosure** - Metadata/instructions/resources properly separated
2. **Mental Model Shift** - Describes skill as canonical approach, not "new feature"
3. **Degree of Freedom** - Matches instructions to declared autonomy level
4. **SKILL.md Conciseness** - Lean, actionable, purpose-driven
5. **Safety & Failure Handling** - Guardrails and recovery steps present
6. **Resource Hygiene** - References current, minimal, discoverable
7. **Consistency** - Terminology and flow clear and unambiguous
8. **Testing Guidance** - Verification steps or examples included
9. **Ownership (Optional)** - Known limitations documented; version/maintainer optional
10. **Tight Scope** - Focused purpose, no feature creep

### 3. Document Findings

Create a review report with:
- ✅ Criteria that pass
- ⚠️  Areas needing improvement
- 🔴 Critical issues requiring fixes
- 💡 Suggestions for enhancement

## Detailed Guidance

For in-depth review criteria and examples:

- **[Quality Checklist](references/quality-checklist.md)** - Comprehensive criteria with examples
- **[Progressive Disclosure](references/progressive-disclosure.md)** - Proper structure and information layering
- **[Mental Model Shift](references/mental-model-shift.md)** - Language and positioning guidance
- **[Common Pitfalls](references/common-pitfalls.md)** - What to avoid and how to fix
- **[Review Examples](references/examples.md)** - Sample reviews demonstrating the process

## Review Workflow

### For New Skills

1. **Structure Check**
   - Verify SKILL.md exists with proper frontmatter
   - Check references/ directory organization
   - Confirm scripts/ are executable if present

2. **Content Review**
   - Frontmatter: name (lowercase, hyphens), description (clear, comprehensive)
   - Body: Concise instructions with examples
   - Progressive disclosure: Core in SKILL.md, details in references/

3. **Quality Assessment**
   - Apply 10-point checklist
   - Verify mental model language
   - Check for appropriate scope and freedom level

### For Updated Skills

1. **Change Assessment**
   - Identify what changed (use git diff if available)
   - Verify changes align with skill's purpose
   - Check for scope creep or complexity additions

2. **Documentation Update**
   - Ensure SKILL.md reflects new capabilities
   - Update references/ if needed
   - Maintain progressive disclosure pattern

3. **Regression Check**
   - Verify existing examples still work
   - Check that changes didn't break mental model
   - Confirm scope remains focused

## Review Report Template

```markdown
# Skill Review: [skill-name]

**Date**: YYYY-MM-DD
**Reviewer**: [name]
**Type**: [New|Update|Audit]

## Summary
Brief overview of the skill and review findings.

## Checklist Results

✅ Progressive Disclosure
✅ Mental Model Shift
⚠️  Degree of Freedom - Instructions too prescriptive for declared high freedom
✅ SKILL.md Conciseness
🔴 Safety & Failure Handling - Missing error recovery steps
✅ Resource Hygiene
✅ Consistency
⚠️  Testing Guidance - Examples present but no verification steps
✅ Ownership
✅ Tight Scope

## Critical Issues

1. **Missing Failure Handling**: Add error recovery steps for [specific scenario]

## Improvements Needed

1. **Degree of Freedom Mismatch**: Reduce prescriptiveness in steps 3-5 to match high freedom declaration
2. **Testing**: Add quick verification example showing expected output

## Suggestions

- Consider moving detailed API reference to references/api-docs.md
- Example in section 4 could be more concise

## Conclusion

[Overall assessment and recommendation: Approve|Needs Revision|Reject]
```

## Best Practices

### Keep SKILL.md Lean

Move detailed content to references/:
- API documentation → `references/api-docs.md`
- Complex workflows → `references/workflows.md`
- Extensive examples → `references/examples.md`
- Configuration details → `references/configuration.md`

### Verify Progressive Disclosure

Check that information loads in stages:
1. **Metadata** (always): name + description only
2. **Instructions** (when triggered): SKILL.md body
3. **Resources** (as needed): references/ files

### Assess Mental Model

Language should reflect "this is the way":
- ❌ "New recommended approach"
- ❌ "Optional feature"
- ✅ "Use [tool] for [task]"
- ✅ "Standard workflow"

### Match Freedom to Instructions

- **High freedom**: Provide principles, let Claude decide specifics
- **Medium freedom**: Offer preferred patterns with parameters
- **Low freedom**: Specify exact steps for fragile operations

## Examples

For complete review examples with before/after comparisons:
- **[Review Examples](references/examples.md)** - Sample reviews of simple and complex skills

For detailed examples of each quality criterion:
- **[Quality Checklist](references/quality-checklist.md)** - Examples for each of the 10 criteria

## Quick Verification

After completing a review, verify the process worked correctly:

**Checklist**:
- [ ] All reference links in SKILL.md resolve correctly
- [ ] Review report follows the template format
- [ ] Critical issues (🔴) are clearly identified
- [ ] At least one improvement or suggestion provided
- [ ] Checklist results show ✅⚠️🔴 indicators

**Smoke test**: Review a simple skill (e.g., a single-file skill with <500 words) and verify you can:
1. Load the skill and identify its structure
2. Apply all 10 checklist criteria
3. Generate a complete review report
4. Identify at least one area for improvement

**Expected outcome**: A review report that provides actionable feedback and follows the template structure.

## Version

**Version**: 1.1.0
**Last Updated**: 2025-11-23
**Maintainer**: Alberto Leal (mail4alberto@gmail.com)
**Changelog**: See `changelogs/skill-reviewer.md` in the marketplace root
