# Common Pitfalls

Common mistakes that reduce skill quality and how to fix them.

## 1. Bloated SKILL.md

### Problem

Including everything in SKILL.md instead of using references/.

**Example**:
```markdown
# API Client

[500 words of background]

## Complete API Documentation
[5000 words of every endpoint]

## All Configuration Options
[2000 words of config details]

## Comprehensive Examples
[50 examples covering every scenario]

## Troubleshooting Guide
[30 common issues]
```

**Impact**:
- Loads 10k+ tokens every time skill triggers
- Context waste for simple tasks
- Harder to maintain
- Difficult to navigate

### Fix

Move detailed content to references/, keep SKILL.md lean:

```markdown
# API Client

## Quick Start

Set API key:
```bash
export API_KEY="your-key"
```

Make request:
```python
response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
```

For complete API documentation, see [api-reference.md](references/api-reference.md).
For configuration options, see [configuration.md](references/configuration.md).
```

**Target**: SKILL.md under 1500 words (~5k tokens)

---

## 2. Duplicate Content

### Problem

Same information repeated in multiple places.

**Example**:

SKILL.md:
```markdown
## Authentication
Set API_KEY environment variable. Get keys from dashboard at https://example.com/keys.
Keys must be 32 hex characters. Rotate every 90 days.
```

references/api-reference.md:
```markdown
## Authentication
Set API_KEY environment variable. Obtain from dashboard...
[same content repeated]
```

**Impact**:
- Wastes tokens
- Maintenance nightmare (update must happen in multiple places)
- Inconsistencies when one copy gets updated

### Fix

Put detailed info in ONE place, link from others:

SKILL.md:
```markdown
## Quick Start

Set API key:
```bash
export API_KEY="your-key"
```

For authentication details, see [api-reference.md](references/api-reference.md#authentication).
```

references/api-reference.md:
```markdown
## Authentication

Obtain API keys from the dashboard at https://example.com/keys.

**Requirements**:
- Format: 32 hexadecimal characters
- Rotation: Every 90 days
- Storage: Environment variable `API_KEY`
...
```

---

## 3. Poor Description in Frontmatter

### Problem

Vague or incomplete description that doesn't help Claude discover when to use the skill.

**Bad examples**:
```yaml
description: PDF tool
```
- Too vague. What does it do with PDFs?

```yaml
description: Extract text from PDFs using pdfplumber library with support for tables and forms
```
- Implementation detail. Doesn't say when to use.

```yaml
description: A helpful utility for working with PDF documents
```
- Generic fluff. No specifics.

### Fix

Include BOTH what it does AND when to use it:

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**Good description formula**:
`[What it does]. Use when [triggering conditions/keywords].`

---

## 4. Missing Safety Warnings

### Problem

Destructive operations without warnings or validation.

**Example**:
```markdown
## Deploy to Production

Run: `./deploy.sh production`
```

**Impact**:
- Users might run dangerous commands accidentally
- No guidance on prerequisites
- No rollback plan

### Fix

Add warnings, validation, and recovery:

```markdown
## Deploy to Production

**⚠️  WARNING**: This deploys to production. Ensure tests pass before proceeding.

**Prerequisites**:
- All tests passing: `make test`
- Code reviewed and merged
- Staging deployment successful

**Deploy**:
```bash
# Verify tests first
make test || { echo "Tests failed"; exit 1; }

# Deploy
./deploy.sh production
```

**If deployment fails**:
1. Check logs: `tail -f /var/log/deploy.log`
2. Rollback: `./deploy.sh rollback`
3. Investigate: Review error messages
```

---

## 5. No Examples or Bad Examples

### Problem

Either no examples, or examples that are too complex/not representative.

**No examples**:
```markdown
## Usage

Use the tool to process files. Various options are available.
```

**Overly complex examples**:
```markdown
## Example

```python
# Complete production-ready example with error handling,
# logging, retries, caching, metrics, and all edge cases
import logging
import time
from functools import wraps
...
[200 lines]
```
```

**Impact**:
- Users don't know how to start
- Complex examples obscure the core pattern

### Fix

Provide minimal, representative examples:

```markdown
## Quick Start

Basic usage:
```python
import tool

result = tool.process("input.txt")
print(result)
```

With options:
```python
result = tool.process("input.txt", format="json", validate=True)
```

For advanced patterns, see [examples.md](references/examples.md).
```

**Good examples are**:
- Minimal (remove non-essential code)
- Representative (show common use case)
- Runnable (actually work if copy-pasted)
- Focused (one concept per example)

---

## 6. Inconsistent Terminology

### Problem

Same concept called by different names throughout the skill.

**Example**:
```markdown
## Creating a Migration

Generate new migration file:
```bash
./create-migration.sh add_users
```

## Running Migrations

Execute all pending schema changes:
```bash
./run-migrations.sh
```

## Rolling Back

Revert the last database modification:
```bash
./undo-migration.sh
```
```

**Terms used**:
- "migration", "schema changes", "database modification"
- "create", "generate"
- "run", "execute"
- "rolling back", "revert", "undo"

**Impact**: Confusing. Users wonder if these are different operations.

### Fix

Use consistent terminology:

```markdown
## Creating a Migration

```bash
./migrate.sh create add_users
```

## Running Migrations

```bash
./migrate.sh apply
```

## Rolling Back Migrations

```bash
./migrate.sh rollback
```
```

**Pick one term and stick to it**:
- Migration (not "schema change" or "database modification")
- Create (not "generate")
- Apply (not "run" or "execute")
- Rollback (not "revert" or "undo")

---

## 7. Scope Creep

### Problem

Skill tries to do too many unrelated things.

**Example**:
```markdown
# Developer Tools

## Features
- Run tests
- Deploy code
- Send emails
- Process images
- Generate reports
- Manage databases
- Create documentation
- Monitor logs
```

**Impact**:
- Unfocused and hard to maintain
- Overlaps with other skills
- Users confused about what it's for

### Fix

Split into focused skills:
- testing-tools → Run tests
- deployment → Deploy code
- email-sender → Send emails
- image-processor → Process images
- etc.

**Each skill should answer**: "What is the one thing this skill does well?"

---

## 8. Over-Prescription (High Freedom Task)

### Problem

Giving step-by-step instructions for a task that needs flexibility.

**Example** (high freedom task with low freedom instructions):
```markdown
## Code Review

1. Check line 1 for indentation
2. Check line 2 for spacing
3. Check line 3 for naming
4. Check line 4 for...
[prescriptive steps for creative task]
```

**Impact**: Constrains Claude unnecessarily, produces robotic results.

### Fix

Provide principles for high freedom tasks:

```markdown
## Code Review

Review code for:
- **Readability**: Clear naming, logical structure, appropriate comments
- **Maintainability**: DRY principle, single responsibility, testable
- **Performance**: Algorithm efficiency, resource usage
- **Security**: Input validation, safe dependencies

Consider the project's context and constraints when making recommendations.
```

---

## 9. Under-Specification (Low Freedom Task)

### Problem

Vague instructions for a fragile operation that needs exact steps.

**Example** (low freedom task with high freedom instructions):
```markdown
## Database Migration

Migrate the database. Make sure everything works.
```

**Impact**: Critical operations fail due to missed steps or wrong order.

### Fix

Provide exact steps for low freedom tasks:

```markdown
## Database Migration

**⚠️  CRITICAL**: Execute in exact order. Do not skip steps.

1. **Backup**:
   ```bash
   ./backup.sh production_db backup_$(date +%Y%m%d).sql
   ```

2. **Test migration**:
   ```bash
   ./migrate.sh --dry-run
   ```
   Verify output shows expected changes.

3. **Apply migration**:
   ```bash
   ./migrate.sh apply
   ```

4. **Verify**:
   ```bash
   ./health-check.sh database
   ```
   Must return "✓ Database healthy".

5. **If failure**:
   ```bash
   ./migrate.sh rollback
   ./restore.sh backup_$(date +%Y%m%d).sql
   ```
```

---

## 10. No Version or Changelog

### Problem

No way to track what changed or what version is current.

**Example**:
```markdown
# API Client

[no version info]
[no changelog]
[no update history]
```

**Impact**:
- Users don't know if they have latest version
- No record of what changed
- Hard to troubleshoot version-specific issues

### Fix

Include version and changelog:

```markdown
# API Client

**Version**: 2.1.0
**Last Updated**: 2025-11-23

...

## Changelog

### 2.1.0 (2025-11-23)
- Add batch request support
- Improve error handling

### 2.0.0 (2025-10-15)
- Breaking: Change authentication method
- Add retry logic

### 1.0.0 (2025-09-01)
- Initial release
```

---

## 11. Broken or Missing Links

### Problem

Links to references/ don't resolve or are missing.

**Example**:

SKILL.md:
```markdown
For details, see [advanced.md](references/advanced.md).
```

But file doesn't exist, or is named differently (`references/advanced-usage.md`).

**Impact**: Users can't access detailed information.

### Fix

Verify all links:

```bash
# Check all markdown links in SKILL.md
grep -o '\[.*\](.*\.md)' SKILL.md | while read link; do
  file=$(echo "$link" | sed 's/.*(\(.*\))/\1/')
  if [[ ! -f "$file" ]]; then
    echo "Broken link: $link"
  fi
done
```

**Best practice**: After creating skill, test all links.

---

## 12. Marketing Language

### Problem

Promotional or fluffy language instead of direct instructions.

**Example**:
```markdown
# Amazing Data Processor

Transform your data workflow with our cutting-edge processing engine! Designed with developers in mind, this powerful tool revolutionizes...

## Why Choose This Tool?

Benefit from industry-leading performance and enterprise-grade reliability...
```

**Impact**: Wastes tokens without providing value.

### Fix

Be direct and actionable:

```markdown
# Data Processor

Process CSV and JSON files with validation and transformation.

## Quick Start

Process CSV file:
```bash
process-data input.csv --format json --validate
```
```

**Cut**:
- Marketing superlatives ("amazing", "revolutionary")
- Benefits lists ("why choose this")
- Generic introductions
- Promotional language

**Keep**:
- What it does
- How to use it
- Actual capabilities

---

## Quick Pitfall Checklist

Run this check on any skill:

**Content**:
- [ ] No marketing fluff or superlatives
- [ ] No duplicate content between files
- [ ] Examples are minimal and representative
- [ ] Instructions match freedom level

**Structure**:
- [ ] SKILL.md under 1500 words
- [ ] Detailed content in references/
- [ ] All links resolve
- [ ] No scope creep (one focused purpose)

**Language**:
- [ ] No "new feature" or "recommended" hedging
- [ ] Consistent terminology throughout
- [ ] Direct, actionable instructions
- [ ] Appropriate warnings for dangerous operations

**Metadata**:
- [ ] Description includes what and when
- [ ] Version and changelog present
- [ ] Clear frontmatter (name, description)

**Safety**:
- [ ] Dangerous operations have warnings
- [ ] Prerequisites stated
- [ ] Failure recovery documented

If any checkbox fails, you've found a pitfall to fix.
