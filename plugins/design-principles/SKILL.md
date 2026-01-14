---
name: design-principles
description: "Guide AI-assisted UI generation toward enterprise-grade, intentional design. Use when building user interfaces, creating dashboards, designing enterprise software or SaaS applications, generating frontend code with styling, or when the user asks for design help. Enforces principles inspired by Linear, Notion, Stripe, and Vercel."
---

# Design Principles

This skill guides AI-assisted UI generation toward enterprise-grade, intentional design rather than producing generic interfaces. It enforces principles inspired by products like Linear, Notion, Stripe, and Vercel.

## When to Use

Invoke this skill when:

- Building user interfaces or frontend components
- Creating dashboards or admin panels
- Designing enterprise software or SaaS applications
- Generating styled frontend code
- User asks for design help or UI improvements
- Working on any project that needs professional, polished styling

## Key Requirement

**Commit to a design direction before coding.** Choose one personality:

| Direction | Character | Use Case |
|-----------|-----------|----------|
| Precision & Density | Tight, monochrome, technical | Developer tools |
| Warmth & Approachability | Generous spacing, soft shadows | Consumer SaaS |
| Sophistication & Trust | Cool tones, layered depth | Enterprise finance |
| Boldness & Clarity | High contrast, dramatic space | Modern dashboards |
| Utility & Function | Muted palette, functional density | GitHub-style tools |
| Data & Analysis | Chart-optimized, numbers-first | Analytics platforms |

## Core Craft Principles

**The 4px grid** governs all spacing (4px → 8px → 12px → 16px → 24px → 32px).

**Symmetrical padding** is mandatory: TLBR values must match unless content creates natural visual balance.

**Depth strategy must be intentional and consistent.** Choose borders-only (flat, technical), subtle single shadows, layered shadows (premium), or surface color shifts—then commit completely.

**Typography hierarchy:** Headlines at 600 weight with tight letter-spacing; body at 400–500; scales from 11px to 32px. Monospace exclusively for data.

**Card layouts should vary internally while maintaining consistent surface treatment.** Border weight, shadow depth, corner radius, and padding remain uniform.

## Critical Details

- Use Phosphor Icons; avoid native form elements
- Animation: 150–250ms with cubic-bezier easing (no bounce)
- Color communicates meaning only (status, action, error, success)
- Dark mode requires border emphasis over shadows
- Include navigation context: sidebars, breadcrumbs, or active states

## The Standard

*"Every interface should look designed by a team that obsesses over 1-pixel differences"*—polished, intentional, never defaulted.

## Attribution

This skill is based on [claude-design-skill](https://github.com/Dammyjay93/claude-design-skill) by Dammyjay93, licensed under MIT.
