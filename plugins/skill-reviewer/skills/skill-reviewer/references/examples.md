# Review Examples

This document provides concrete examples of using skill-reviewer to review different types of skills.

## Example 1: Simple Skill Review

### Skill Being Reviewed

**Name**: commit-helper
**Type**: Single-file skill (SKILL.md only, 287 words)
**Purpose**: Generate git commit messages from staged changes

### Review Process

**Step 1: Load the skill**
```bash
cat ~/.claude/skills/commit-helper/SKILL.md
```

**Step 2: Check structure**
- ✅ SKILL.md exists with valid frontmatter
- ✅ No supporting files (appropriate for simple skill)
- Word count: 287 words (19% of 1500-word budget)

**Step 3: Apply 10-point checklist**

1. ✅ **Progressive Disclosure**: All content in SKILL.md (appropriate for simple skill)
2. ✅ **Mental Model Shift**: "Use when writing commit messages" (canonical)
3. ✅ **Degree of Freedom**: Medium freedom with suggested patterns
4. ✅ **SKILL.md Conciseness**: 287 words, lean and focused
5. ✅ **Safety**: N/A (read-only git commands)
6. ✅ **Resource Hygiene**: N/A (no references)
7. ✅ **Consistency**: Clear terminology throughout
8. ⚠️  **Testing Guidance**: No example output or verification steps
9. 🔴 **Ownership**: Missing version and maintainer info
10. ✅ **Tight Scope**: Focused solely on commit messages

### Review Report

```markdown
# Skill Review: commit-helper

**Date**: 2025-11-23
**Reviewer**: Jane Doe
**Type**: New

## Summary

Simple, well-structured skill for generating commit messages. Appropriate use of single-file structure for focused task. Missing ownership metadata and testing examples.

## Checklist Results

✅ Progressive Disclosure
✅ Mental Model Shift
✅ Degree of Freedom
✅ SKILL.md Conciseness
✅ Safety & Failure Handling
✅ Resource Hygiene
✅ Consistency
⚠️  Testing Guidance - No example output
🔴 Ownership - Missing version/maintainer
✅ Tight Scope

## Critical Issues

1. **Missing Ownership**: Add version, date, and maintainer information

## Improvements Needed

1. **Testing Examples**: Add example of generated commit message format

## Suggestions

- Consider adding example output showing the format of generated commit messages
- Add quick verification checklist at the end

## Conclusion

**Needs Revision** - Minor fixes needed for ownership metadata and testing guidance. Otherwise well-structured for its scope.
```

## Example 2: Complex Skill Review

### Skill Being Reviewed

**Name**: pdf-processing
**Type**: Multi-file skill with scripts
**Purpose**: Extract text, fill forms, merge PDFs

### Review Process

**Step 1: Load the skill**
```bash
ls -la ~/.claude/skills/pdf-processing/
cat ~/.claude/skills/pdf-processing/SKILL.md
```

**Step 2: Check structure**
```
pdf-processing/
├── SKILL.md (542 words)
├── FORMS.md (824 words)
├── REFERENCE.md (1,453 words)
└── scripts/
    ├── fill_form.py
    └── validate.py
```

Total: 2,819 words across 3 markdown files

**Step 3: Apply 10-point checklist**

1. ⚠️  **Progressive Disclosure**: Too much detail in SKILL.md (542 words could be leaner)
2. ✅ **Mental Model Shift**: "Use for PDF files" (canonical language)
3. ✅ **Degree of Freedom**: High freedom with code examples
4. ⚠️  **SKILL.md Conciseness**: 542 words (36% of budget, but includes code)
5. ⚠️  **Safety**: Scripts lack input validation warnings
6. ✅ **Resource Hygiene**: Clear references, organized structure
7. ✅ **Consistency**: Consistent terminology
8. ✅ **Testing Guidance**: Examples with expected outputs
9. ✅ **Ownership**: Version 2.1.0, maintained by team
10. 🔴 **Tight Scope**: Scope creep - includes Excel parsing (should be separate skill)

### Review Report

```markdown
# Skill Review: pdf-processing

**Date**: 2025-11-23
**Reviewer**: John Smith
**Type**: Update

## Summary

Well-organized multi-file skill with good progressive disclosure structure. Scope has expanded beyond PDFs to include Excel processing, which should be separated. Some safety warnings needed for file operations.

## Checklist Results

⚠️  Progressive Disclosure - SKILL.md could be leaner (move some code to REFERENCE.md)
✅ Mental Model Shift
✅ Degree of Freedom
⚠️  SKILL.md Conciseness - 542 words (could reduce to ~400)
⚠️  Safety & Failure Handling - Scripts need input validation warnings
✅ Resource Hygiene
✅ Consistency
✅ Testing Guidance
✅ Ownership
🔴 Tight Scope - Includes Excel parsing (out of scope)

## Critical Issues

1. **Scope Creep**: Remove Excel parsing functionality and create separate skill
   - Current: PDF + Excel in one skill (confusing)
   - Recommended: Split into pdf-processing and excel-processing

## Improvements Needed

1. **Progressive Disclosure**: Move detailed code examples from SKILL.md to REFERENCE.md
   - Keep only quick start example in SKILL.md
   - Move API details and advanced examples to REFERENCE.md

2. **Safety Warnings**: Add warnings for file operations
   - Warn about overwriting files in merge operations
   - Add note about validating PDF inputs before processing

3. **SKILL.md Conciseness**: Reduce from 542 to ~400 words
   - Keep Quick Start section
   - Move detailed examples to REFERENCE.md

## Suggestions

- Consider adding TROUBLESHOOTING.md for common errors
- Example in fill_form.py could use more comments
- Update description to remove Excel references

## Conclusion

**Needs Revision** - Critical scope creep issue must be addressed by removing Excel functionality. Otherwise solid skill with good structure.
```

## Example 3: Quick Audit Review

### Skill Being Reviewed

**Name**: code-reviewer
**Type**: Single-file skill
**Purpose**: Review code for best practices

### Quick Review (5-minute audit)

**Focus areas for quick audit**:
1. Progressive Disclosure ✅
2. Mental Model Shift ✅
3. Ownership 🔴
4. Tight Scope ✅

### Quick Findings

```markdown
# Quick Audit: code-reviewer

**Date**: 2025-11-23
**Type**: Audit

## Quick Check

✅ Progressive Disclosure - Appropriate for single file
✅ Mental Model Shift - Canonical language
🔴 Ownership - Missing version info
✅ Tight Scope - Focused on code review

## Action Items

1. Add version and maintainer information
2. Consider full review for other criteria

## Status

**Quick Fix Needed** - Add ownership metadata
```

## Example 4: Before/After Improvement

### Before: Skill with Issues

```yaml
---
name: data-processor
description: Helps with data
---

# Data Processor

## What This Does

This is a new recommended tool for processing data files. You might want to use it when working with CSV, JSON, Excel, or database exports.

## How to Use

1. Load your file
2. Pick what you want to do:
   - Clean the data
   - Transform the data
   - Validate the data
   - Export the data
3. Run the processing
4. Check the results

## Advanced Features

You can also use the advanced mode by setting the config...
[500 more words of detailed configuration]

## Notes

Make sure Python is installed.
```

**Issues identified**:
- ❌ Vague description ("Helps with data")
- ❌ Mental model issues ("new recommended tool", "You might want to")
- ❌ Too broad scope (CSV, JSON, Excel, databases)
- ❌ No progressive disclosure (all details in SKILL.md)
- ❌ Missing ownership information

### After: Improved Version

```yaml
---
name: csv-analyzer
description: Analyze CSV files for data quality issues, missing values, and statistical summaries. Use when working with CSV data, data quality checks, or data profiling.
---

# CSV Analyzer

## Quick Start

Analyze a CSV file for quality issues:
```python
import pandas as pd
df = pd.read_csv("data.csv")
# I'll check for missing values, duplicates, and provide summary statistics
```

## Common Operations

- Data quality assessment
- Missing value detection
- Statistical summaries
- Duplicate identification

For detailed configuration options, see [configuration.md](references/configuration.md).
For examples of quality checks, see [examples.md](references/examples.md).

## Requirements

Requires pandas:
```bash
pip install pandas
```

## Quick Verification

- [ ] Successfully reads CSV file
- [ ] Reports missing values accurately
- [ ] Provides statistical summary

## Version

**Version**: 1.0.0
**Last Updated**: 2025-11-23
**Maintainer**: team@example.com
**Changelog**: See changelog.md
```

**Improvements**:
- ✅ Specific description with trigger keywords
- ✅ Canonical language ("Use when", direct instructions)
- ✅ Tight scope (CSV only, not all data formats)
- ✅ Progressive disclosure (details in references/)
- ✅ Ownership information included
- ✅ Testing verification checklist

## Tips for Effective Reviews

### Use the Right Review Type

**Quick Audit** (5 minutes):
- Check 4 key criteria: Progressive Disclosure, Mental Model, Ownership, Scope
- Good for marketplace-wide audits
- Identifies critical issues only

**Standard Review** (15-20 minutes):
- Apply all 10 checklist criteria
- Good for new skills and significant updates
- Provides comprehensive feedback

**Deep Review** (30+ minutes):
- Full checklist plus detailed examples testing
- Review all reference files
- Test any included scripts
- Good for complex multi-file skills

### Focus on High-Impact Issues

**Critical (must fix)**:
- Scope creep / overlapping functionality
- Missing safety warnings for dangerous operations
- Broken mental model (describing as "optional" or "new")

**Important (should fix)**:
- Missing ownership metadata
- Poor progressive disclosure (bloated SKILL.md)
- Vague description

**Nice to have**:
- Additional examples
- Minor wording improvements
- Formatting consistency

### Common Patterns

**Pattern: Marketing Language**
```markdown
❌ Before: "This amazing skill revolutionizes how you work with PDFs!"
✅ After: "Extract text and fill forms in PDF files."
```

**Pattern: Optional Framing**
```markdown
❌ Before: "You can optionally use this skill when you need to..."
✅ After: "Use for commit message generation from git diffs."
```

**Pattern: Scope Creep**
```markdown
❌ Before: "Process PDFs, Word docs, Excel files, and images"
✅ After: "Process PDF files" (separate skills for other formats)
```
