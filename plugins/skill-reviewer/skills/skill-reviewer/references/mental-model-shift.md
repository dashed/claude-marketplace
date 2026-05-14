# Mental Model Shift

Guide to positioning skills as canonical approaches rather than optional features.

## The Principle

When a skill provides a better way to do something, the documentation should reflect confidence in that approach. The feature isn't "new" or "recommended"—it IS the way things are done.

**Mental model shift means**:
- Feature becomes "the way" (not "a new way")
- Documentation reflects this confidence
- Alternative approaches are downgraded to "manual" or "advanced"

## Language Patterns

### ✅ Canonical Language (Good)

**Presents as THE way**:
```markdown
# Session Registry

Use the session registry for automatic session tracking.

## Quick Start
1. Create session: `create-session.sh -n my-session`
2. Send commands: `safe-send.sh -s my-session -c "command"`
```

**Key phrases**:
- "Use [tool] for [task]"
- "Standard workflow"
- "[Tool] handles [task]"
- Direct imperatives ("Create a session", "Send commands")

---

### ❌ Optional Language (Bad)

**Presents as A way among many**:
```markdown
# Session Registry (NEW!)

The session registry is a new recommended feature you can use instead of manual socket management.

## Two Approaches

### Traditional: Manual Socket Management
[old way]

### New (Recommended): Session Registry
[new way]

You might want to consider using the session registry...
```

**Red flag phrases**:
- "New feature" or "NEW!"
- "Recommended" or "optional"
- "You can use" or "you might want to"
- "Instead of" or "alternative to"
- Side-by-side old vs new comparisons
- "Traditional" vs "modern"

---

## Documentation Structure

### Primary Workflow First

Place the canonical approach at the top as the default.

**Good structure**:
```markdown
# Tool Name

## Quick Start
[Canonical approach]

## Common Tasks
[Using canonical approach]

---

## Alternative: Manual Approach

For advanced users or special cases...
```

**Bad structure**:
```markdown
# Tool Name

## Choose Your Approach

### Option 1: Traditional Method (Still Supported)
[Old way]

### Option 2: New Registry Method (Recommended!)
[New way]
```

---

### Downgrade Alternatives

When mentioning alternative approaches, position them as secondary.

**Good** (alternative is clearly secondary):
```markdown
# Session Management

Create and manage sessions using the session registry.

## Creating Sessions
```bash
create-session.sh -n my-session --python
```

---

## Manual Socket Management

For advanced use cases requiring explicit socket control, you can manage sockets manually.
See [manual-socket-management.md](references/manual-socket-management.md).
```

**Bad** (alternatives treated equally):
```markdown
# Session Management

## Approach 1: Registry (Recommended)
Use create-session.sh...

## Approach 2: Manual Sockets (Traditional)
Create sockets manually...

Both approaches are fully supported. Choose based on your preferences.
```

---

## Evolution Example: tmux Skill

### Phase 1: Feature Addition (❌ Wrong)

```markdown
# tmux Skill

## New Feature: Session Registry!

We're excited to announce session registry support! This new recommended feature eliminates the need for manual socket management.

### Traditional Workflow (Still Supported)
1. Create socket: `tmux -S /tmp/my.sock new -d`
2. Send commands: `tmux -S /tmp/my.sock send-keys...`

### New Registry Workflow (Recommended!)
1. Create session: `create-session.sh -n my-session`
2. Send commands: `safe-send.sh -s my-session -c "command"`

Consider migrating to the registry for a better experience!
```

**Problems**:
- "New feature" announcement
- "Recommended" implies optionality
- Side-by-side comparison treats both as equal
- "Consider migrating" is hesitant

---

### Phase 2: Mental Model Shift (✅ Right)

```markdown
# tmux Skill

Use the session registry for automatic session tracking.

## Quick Start

Create a session:
```bash
create-session.sh -n my-session --python
```

Send commands:
```bash
safe-send.sh -s my-session -c "print('hello')"
```

Wait for output:
```bash
wait-for-text.sh -s my-session -p ">>>"
```

## Session Management

List sessions:
```bash
list-sessions.sh
```

Clean up dead sessions:
```bash
cleanup-sessions.sh --dead
```

---

## Alternative: Manual Socket Management

For advanced scenarios requiring explicit socket control, see [manual-sockets.md](references/manual-sockets.md).
```

**Improvements**:
- No "new" or "recommended" language
- Registry is THE approach
- Direct, confident instructions
- Manual approach relegated to "Alternative" section
- Documentation reflects "this is the way"

---

## Key Transformations

### From Feature to Standard

**Before**: "Session registry is a new feature"
**After**: "Use the session registry"

**Before**: "You can optionally use create-session.sh"
**After**: "Create sessions with create-session.sh"

**Before**: "The recommended approach is..."
**After**: [Just describe the approach as the default]

### From Optional to Canonical

**Before**: "Consider using -s flag for convenience"
**After**: "Use -s flag to specify the session"

**Before**: "The -s flag is a shorthand that may be helpful"
**After**: "The -s flag identifies the session by name"

### From Hedging to Direct

**Before**: "You might want to try the session registry"
**After**: "The session registry tracks sessions automatically"

**Before**: "It's recommended to clean up dead sessions regularly"
**After**: "Clean up dead sessions with cleanup-sessions.sh"

---

## Section Positioning

### Primary Content (80-90% of docs)

Focus on the canonical approach:
- Quick start
- Common workflows
- Standard examples
- Main documentation

### Alternative Content (10-20% of docs)

Relegated to end or separate files:
- "Alternative:" sections
- "Advanced:" sections
- "Manual:" approaches
- Legacy compatibility

---

## Migration Guidance

When transitioning from old to new approach:

### During Migration

Acknowledge the transition but frame it positively:

```markdown
# Tool Name

Use [new approach] for [task].

## Migrating from Manual Approach

If you're currently using manual [old approach]:
1. Replace [old command] with [new command]
2. Remove [old pattern]
3. Adopt [new pattern]

Migration is straightforward and improves [benefit].
```

### After Migration Period

Remove migration notices, treat new approach as standard:

```markdown
# Tool Name

Use [new approach] for [task].

## Alternative: Manual Approach
For advanced cases, see [manual.md](references/manual.md).
```

---

## Verification Checklist

Mental model shift audit:

Language:
- [ ] No "new feature" or "NEW!" markers
- [ ] No "recommended" or "optional" hedging
- [ ] No side-by-side old vs new comparisons
- [ ] Direct, imperative instructions
- [ ] Confident tone throughout

Structure:
- [ ] Canonical approach presented first
- [ ] Primary content focuses on canonical approach
- [ ] Alternatives relegated to end or separate files
- [ ] Section titles don't imply choice ("Quick Start" not "Option 1")

Content:
- [ ] Examples use canonical approach
- [ ] Workflow descriptions assume canonical approach
- [ ] Troubleshooting assumes canonical approach
- [ ] Getting started uses canonical approach

---

## Common Mistakes

### Mistake 1: Hedging with "Recommended"

❌ "The recommended way is to use the registry"
✅ "Use the registry for session management"

**Why**: "Recommended" implies other approaches are equally valid.

### Mistake 2: Feature Announcement Language

❌ "We're introducing session registry support"
✅ "Session registry provides automatic session tracking"

**Why**: "Introducing" or "new" frames it as optional addition.

### Mistake 3: Choice Architecture

❌ "Choose between registry or manual approach based on your needs"
✅ "Use registry for session management. For advanced cases requiring manual control, see..."

**Why**: Presenting choice implies both are equal. Default should be clear.

### Mistake 4: Qualification

❌ "Session registry can help you manage sessions more easily"
✅ "Session registry manages sessions automatically"

**Why**: "Can help" and "more easily" undermine confidence.

### Mistake 5: Comparison to Old Way

❌ "Unlike manual socket management, session registry is automatic"
✅ "Session registry tracks sessions automatically"

**Why**: Mentioning the old way keeps it in the mental model.

---

## Summary

**Mental model shift means**:
- Documentation reflects the feature as canonical
- Language is direct and confident
- Alternatives are clearly secondary
- No hedging or option-presenting

**Key transformation**:
- From: "New recommended feature you can optionally use"
- To: "This is how you do it"

**Test**: Read your documentation. If someone unfamiliar with the history would see multiple equally-presented approaches, the mental model shift is incomplete.
