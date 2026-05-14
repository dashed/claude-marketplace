---
name: ultrathink
description: "Invoke deep sequential thinking for complex problem-solving. Use when the user says 'use ultrathink', 'ultrathink', or when tackling problems that require careful step-by-step reasoning, planning, hypothesis generation, or multi-step analysis."
license: MIT
---

# Ultrathink

Ultrathink activates the Sequential Thinking MCP tool (`mcp__sequential_thinking__sequentialthinking`) to enable deep, structured reasoning through complex problems.

## When to Use

Invoke ultrathink when:

- User explicitly requests it ("use ultrathink", "ultrathink this")
- Complex problems requiring step-by-step decomposition
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where full scope isn't initially clear
- Multi-step solutions requiring maintained context
- Situations requiring hypothesis generation and verification

## How to Use

Call the sequential thinking tool with structured thoughts:

```
mcp__sequential_thinking__sequentialthinking:
  thought: "Your current thinking step"
  nextThoughtNeeded: true/false
  thoughtNumber: 1
  totalThoughts: 5 (estimate, can adjust)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thought` | string | Yes | Current thinking step - analysis, revision, question, or realization |
| `nextThoughtNeeded` | boolean | Yes | True if more thinking needed, false when done |
| `thoughtNumber` | integer | Yes | Current thought number in sequence |
| `totalThoughts` | integer | Yes | Estimated total thoughts (can adjust up/down) |
| `isRevision` | boolean | No | Whether this revises previous thinking |
| `revisesThought` | integer | No | Which thought number is being reconsidered |
| `branchFromThought` | integer | No | Branching point thought number |
| `branchId` | string | No | Branch identifier |
| `needsMoreThoughts` | boolean | No | Signal that more thoughts needed at "end" |

### Key Capabilities

1. **Dynamic adjustment**: Revise total thought count as understanding evolves
2. **Revision support**: Question or revise previous thoughts
3. **Branching**: Explore alternative approaches from any point
4. **Hypothesis cycle**: Generate hypothesis, verify, repeat until satisfied
5. **Non-linear thinking**: Don't need to build linearly - can backtrack

### Process Pattern

1. Start with initial estimate of needed thoughts
2. Break down the problem systematically
3. Question or revise previous thoughts as needed
4. Generate solution hypotheses when appropriate
5. Verify hypotheses against the chain of thought
6. Add more thoughts if needed, even at the "end"
7. Express uncertainty when present
8. Set `nextThoughtNeeded: false` only when truly done

### Example

```
Thought 1: "Let me analyze this authentication bug. The user reports login failures after password reset..."
Thought 2: "Looking at the code flow: reset generates token -> user clicks link -> new password set. The issue might be..."
Thought 3: "Hypothesis: The session isn't being invalidated after password change. Let me verify..."
Thought 4 (revision): "Actually, reconsidering thought 2 - the token expiry might be the issue, not session..."
Thought 5: "Verified: Token expiry is set to 1 hour but email delivery can take longer. Solution: extend to 24 hours."
```

## Best Practices

- Start with reasonable thought estimate (3-7 for most problems)
- Don't hesitate to revise or add thoughts
- Mark revisions with `isRevision: true` and `revisesThought: N`
- Express uncertainty rather than guessing
- Use branching for exploring alternatives
- Only set `nextThoughtNeeded: false` when confident in solution
