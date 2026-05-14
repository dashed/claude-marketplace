# Quality Checklist - Detailed Criteria

Comprehensive quality criteria for skill review with examples and guidance.

## 1. Progressive Disclosure

**What to check**: Information is properly layered across metadata, instructions, and resources.

**Good example**:
```yaml
---
name: pdf-processor
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files.
---

# PDF Processor

## Quick Start
Use pdfplumber to extract text:
```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

For form filling, see [forms.md](references/forms.md).
For advanced table extraction, see [tables.md](references/tables.md).
```

**Bad example**:
```markdown
# PDF Processor

## Complete API Reference
[500 lines of pdfplumber API documentation inline...]

## All Possible Workflows
[50 different use cases with full code...]

## Configuration Options
[Every configuration parameter explained...]
```

**Why it matters**: Skills should load incrementally. Metadata is always loaded (tiny), SKILL.md loads when triggered (small), references load as needed (can be large).

**Review questions**:
- Is SKILL.md under 5k tokens?
- Are detailed references offloaded to separate files?
- Does SKILL.md link to references instead of duplicating content?

---

## 2. Mental Model Shift

**What to check**: Skill is described as the canonical way, not a "new" or "recommended" feature.

**Good example**:
```markdown
# Session Registry

Use the session registry for automatic session tracking. This eliminates manual socket management.

## Standard Workflow
1. Create a session: `create-session.sh -n my-session`
2. Use the session: `safe-send.sh -s my-session -c "command"`
```

**Bad example**:
```markdown
# Session Registry (NEW!)

The session registry is a new recommended feature that you can optionally use instead of manual socket management.

## Two Approaches
### Approach 1: Manual Socket Management (Traditional)
[old way...]

### Approach 2: Session Registry (Recommended!)
[new way...]
```

**Why it matters**: Mental model shift means the feature becomes "the way" things are done, not an alternative. Documentation should reflect this confidence.

**Red flags**:
- "New feature" or "recommended approach"
- Side-by-side comparisons of old vs new
- Hedging language ("you might want to", "consider using")
- "Traditional" or "legacy" alongside "new"

**Review questions**:
- Does the documentation present this as THE way to do the task?
- Is old/alternative approach relegated to a "Manual Alternative" section?
- Does language convey confidence rather than optionality?

---

## 3. Degree of Freedom

**What to check**: Instructions match the declared autonomy level (high/medium/low).

**High Freedom** (principles and heuristics):
```markdown
## Analyzing Code Quality

Review code for:
- Readability and maintainability
- Performance implications
- Security concerns
- Test coverage

Consider the project's context and constraints when making recommendations.
```

**Medium Freedom** (preferred patterns with parameters):
```markdown
## Creating Tests

Use pytest with this structure:
```python
def test_feature_name():
    # Arrange: Setup test data
    # Act: Execute the feature
    # Assert: Verify results
```

Adjust assertion strictness based on feature criticality.
```

**Low Freedom** (specific steps):
```markdown
## Deploying to Production

Execute exactly in order:
1. Run: `make test` (must pass 100%)
2. Run: `make build`
3. Tag release: `git tag v1.x.x`
4. Push: `git push origin v1.x.x`
5. Run: `./deploy.sh production`
6. Monitor: `tail -f /var/log/app.log` for 5 minutes
```

**Why it matters**: Mismatch creates confusion. High freedom tasks shouldn't be over-specified. Low freedom tasks shouldn't be under-specified.

**Review questions**:
- Is the freedom level explicitly stated or clearly implied?
- Do instructions match that freedom level?
- Are fragile operations given low freedom with exact steps?
- Are creative/contextual tasks given high freedom?

---

## 4. SKILL.md Conciseness

**What to check**: SKILL.md is lean, actionable, and purpose-driven.

**Good example** (concise):
```markdown
# API Client

## Authentication
Set `API_KEY` environment variable before making requests.

## Making Requests
```python
import requests
response = requests.get(
    "https://api.example.com/data",
    headers={"Authorization": f"Bearer {os.getenv('API_KEY')}"}
)
```

For all endpoints and parameters, see [api-reference.md](references/api-reference.md).
```

**Bad example** (verbose):
```markdown
# API Client

## Introduction
This skill helps you interact with the Example API. The API provides various endpoints for data access and manipulation. Founded in 2020, Example Corp offers...

## Why Use This Skill
Benefits of using this skill include...
- Consistent authentication
- Error handling
- Rate limiting
[more marketing copy...]

## Prerequisites
Before you begin, make sure you have:
1. An API key (see below for how to obtain)
2. Python 3.7+ installed
3. requests library (can be installed via pip)
4. A stable internet connection
...
```

**Why it matters**: Context window is expensive. Every word should earn its place.

**Conciseness checklist**:
- ❌ Marketing language or lengthy introductions
- ❌ Redundant explanations of obvious concepts
- ❌ Walls of text that could be examples
- ✅ Direct, actionable instructions
- ✅ Minimal but representative examples
- ✅ Links to references for depth

**Review questions**:
- Could any section be condensed by 50% without losing clarity?
- Are there marketing phrases or fluff?
- Do examples replace explanations where possible?
- Is depth offloaded to references/?

---

## 5. Safety & Failure Handling

**What to check**: Guardrails for dangerous actions, clear failure modes, recovery steps.

**Good example**:
```markdown
## Deploying Changes

**⚠️  WARNING**: This deploys to production. Ensure tests pass before proceeding.

```bash
# Verify tests first
make test || { echo "Tests failed - aborting"; exit 1; }

# Deploy
./deploy.sh production
```

**If deployment fails**:
1. Check logs: `tail -f /var/log/deploy.log`
2. Rollback: `./deploy.sh rollback`
3. Verify: `curl https://api.example.com/health`

**Rollback steps**:
```bash
git revert HEAD
./deploy.sh production
```
```

**Bad example**:
```markdown
## Deploying Changes

Run: `./deploy.sh production`
```

**Why it matters**: Skills often perform critical or destructive operations. Users need to know what can go wrong and how to recover.

**Safety elements**:
- **Warnings** for destructive operations
- **Validation** steps before critical actions
- **Failure modes** documented
- **Recovery procedures** provided
- **Assumptions** stated explicitly

**Review questions**:
- Are dangerous operations flagged with warnings?
- Are there validation steps before destructive actions?
- Are failure scenarios documented?
- Are rollback/recovery steps provided?

---

## 6. Resource Hygiene

**What to check**: References are current, minimal, discoverable, and properly linked.

**Good example**:
```
skill-name/
├── SKILL.md
└── references/
    ├── api-reference.md (current, focused)
    ├── examples.md (representative cases)
    └── troubleshooting.md (common issues)
```

SKILL.md properly links:
```markdown
See [API Reference](references/api-reference.md) for all endpoints.
For common issues, check [Troubleshooting](references/troubleshooting.md).
```

**Bad example**:
```
skill-name/
├── SKILL.md
└── references/
    ├── docs.md (duplicates SKILL.md)
    ├── api-v1.md (outdated)
    ├── api-v2.md (current but not clear)
    ├── examples-old.md (deprecated)
    ├── examples-new.md (current)
    ├── random-notes.md (unclear purpose)
    └── README.md (redundant)
```

**Resource hygiene checklist**:
- ✅ Each file has clear, unique purpose
- ✅ File names indicate content
- ✅ No duplicate information
- ✅ Links from SKILL.md resolve
- ✅ No outdated or deprecated content
- ✅ Secret handling documented if applicable

**Review questions**:
- Is each reference file's purpose clear from its name?
- Are all links from SKILL.md valid?
- Is there duplicate content between files?
- Are outdated resources removed?

---

## 7. Consistency & Clarity

**What to check**: Terminology consistent, flow logical, formatting readable.

**Good example**:
```markdown
# Database Migration Tool

## Running Migrations

Apply all pending migrations:
```bash
./migrate.sh apply
```

Rollback the last migration:
```bash
./migrate.sh rollback
```

## Migration Files

Create new migration:
```bash
./migrate.sh create add_users_table
```

This creates `migrations/001_add_users_table.sql`.
```

**Bad example**:
```markdown
# Database Migration Tool

## Executing Migrations

Run migrations using the migration runner:
```bash
./run-migrations.sh
```

## Reverting Changes

Undo schema modifications:
```bash
./rollback-db.sh
```

## Creating Migration Scripts

Generate new migration file:
```bash
./new-migration.sh
```
```

**Consistency issues** in bad example:
- Command names inconsistent (`./migrate.sh` vs `./run-migrations.sh`)
- Terminology varies ("migrations" vs "schema modifications")
- Section headings use different patterns

**Clarity checklist**:
- ✅ Consistent terminology throughout
- ✅ Logical section ordering
- ✅ Clear, unambiguous instructions
- ✅ Readable formatting and spacing
- ✅ No conflicting guidance

**Review questions**:
- Is the same concept called by the same name throughout?
- Do sections flow in logical order?
- Are commands/tools referenced consistently?
- Is formatting consistent?

---

## 8. Testing & Verification

**What to check**: Quick checks, expected outputs, or smoke tests included.

**Good example**:
```markdown
## Verification

Test the installation:
```bash
./health-check.sh
```

**Expected output**:
```
✓ API connection successful
✓ Database accessible
✓ Cache configured
All systems operational
```

**Quick smoke test**:
```bash
# Should return status 200
curl -I https://api.example.com/health
```
```

**Bad example**:
```markdown
## Usage

Run the tool:
```bash
./tool.sh
```
```

**Why it matters**: Users need to verify the skill works correctly and understand what success looks like.

**Testing elements**:
- **Smoke tests**: Quick checks that basic functionality works
- **Expected outputs**: What success looks like
- **Verification steps**: How to confirm it's working
- **Example runs**: Representative use cases with results

**Review questions**:
- Are there quick verification steps?
- Is expected output shown?
- Can users confirm the skill works?
- Are examples testable/reproducible?

---

## 9. Ownership & Maintenance (Optional)

**What to check**: Known limitations documented. Version/maintainer metadata optional but recommended for team/public skills.

**Note**: Marketplace-level changelogs (changelogs/skill-name.md) are required per marketplace standards and provide versioning at the marketplace level. The Version section within SKILL.md itself is optional.

**When to include version metadata in SKILL.md**:
- Public marketplace skills (helps users track updates)
- Team-shared skills (clarifies who maintains it)
- Skills with frequent breaking changes (version tracking important)

**When to skip version metadata in SKILL.md**:
- Personal skills for individual use
- Experimental/prototype skills
- Skills where marketplace changelogs provide sufficient tracking

**Example with optional version metadata**:
```markdown
# API Integration Skill

**Version**: 1.2.0
**Maintainer**: DevTools Team (devtools@example.com)

## Known Limitations

- Rate limited to 100 requests/minute
- Large file uploads (>10MB) not supported
- Requires Python 3.8+
```

**Minimal example (recommended for most skills)**:
```markdown
# Simple Helper Skill

## Known Limitations

- Works only on Linux/macOS
- Requires bash 4.0+
```

**Why it matters**: Known limitations help users understand constraints. Version metadata in SKILL.md is helpful for team coordination but optional.

**Core elements**:
- **Known Limitations** (recommended): Document constraints and requirements
- **Version** (optional): Current version number
- **Maintainer** (optional): Contact info for questions
- **Changelog** (optional in SKILL.md): Can reference marketplace changelog or references/

**Review questions**:
- Are known limitations or requirements documented?
- If version metadata is present, is it complete and current?
- If this is a team skill, is maintainer contact info provided?

---

## 10. Tight Scope & Minimalism

**What to check**: Focused purpose, no feature creep, no overlapping functionality.

**Good example** (focused):
```markdown
# PDF Text Extractor

Extract text content from PDF files using pdfplumber.

## Supported Operations
- Extract text from single page
- Extract text from all pages
- Extract text with layout preservation

**Not covered** (use pdf-form-filler skill):
- Form filling
- PDF editing
```

**Bad example** (scope creep):
```markdown
# PDF Swiss Army Knife

Complete PDF toolkit for all your document needs!

## Features
- Text extraction
- Image extraction
- Form filling
- PDF editing
- PDF merging
- PDF splitting
- Watermarking
- OCR processing
- Compression
- Encryption
- Digital signatures
- Conversion to Word/Excel
- Email integration
- Cloud storage sync
```

**Why it matters**: Focused skills are easier to maintain, understand, and use. Feature creep dilutes the skill's purpose and increases complexity.

**Scope checklist**:
- ✅ Solves one focused job well
- ✅ Clear boundaries (what's in, what's out)
- ✅ No overlapping functionality with other skills
- ✅ No unrelated features
- ✅ Complexity matches the actual need

**Review questions**:
- Does the skill do one thing well?
- Are there unrelated features that should be separate skills?
- Does functionality overlap with existing skills?
- Is complexity justified by the use case?

---

## Using This Checklist

### Quick Review (5-10 minutes)

Scan for obvious issues:
1. Check SKILL.md length (should be under 5k tokens)
2. Verify progressive disclosure (links to references/)
3. Look for mental model language ("new feature", "recommended")
4. Check for safety warnings on destructive operations
5. Verify examples are present and minimal

### Thorough Review (30-60 minutes)

Apply all 10 criteria systematically:
1. Read SKILL.md completely
2. Check frontmatter quality
3. Verify each criterion with examples
4. Review all reference files
5. Test examples if possible
6. Document findings in review report

### Common Review Patterns

**New Skill**:
- Focus on criteria 1, 2, 4, 10 (structure and scope)
- Verify progressive disclosure from the start
- Ensure mental model language is correct

**Updated Skill**:
- Focus on criteria 3, 7, 9 (consistency with changes)
- Check that updates didn't break existing patterns
- Verify changelog is updated

**Audit**:
- Apply all 10 criteria
- Compare against other skills for consistency
- Look for improvement opportunities
