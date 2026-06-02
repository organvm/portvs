---
name: portal-router
description: Resolve and load any agent capability across the whole fleet from one place. Given an intent, finds the matching skill/command/agent across Claude, Codex, Gemini, .agents, a-i--skills, OpenCode, and OpenClaw — then loads it through the _arms portal. Triggers on cross-agent skill discovery, "which agent has a skill for X", capability routing, or "find a skill that does Y".
license: MIT
governance_phases: [frame, build]
governance_norm_group: repo-hygiene
organ_affinity: [organ-iv]
triggers: [cross-agent-skill-discovery, capability-routing, find-a-skill, which-agent-has, portal-resolve]
complements: [agent-swarm-orchestrator, multi-agent-workforce-planner]
status: promoted
promoted_to: a-organvm/a-i--skills · skills/tools/portal-router via PR #20 (squash-merged 2026-05-30 as 1a36d81; admin override past the branch-protection review gate). Loads natively from ~/.claude/skills/portal-router and reflects through mirror/claude; confirmed present in the harness skill registry. The live arm remains ~/_arms/arm.
---

# portal-router — the first forged arm

This is `_arms`' own first capability — not borrowed from any vendor ecosystem,
forged because `_arms` is the **only vantage point that sees all agents at once**.
Every other skill belongs to one agent. This one belongs to the portal, and its
job is to make the portal *operational*: turn the eight mirrored ecosystems from
a thing you look at into a thing you route through.

## What it does

Given an intent, it searches **every** mirrored ecosystem plus our own Zone-1
skills, normalizes their heterogeneous unit shapes (Claude `SKILL.md` dirs,
OpenCode flat command `.md`, a-i--skills `*.skill/` dirs, OpenClaw agents…) into
one record, ranks matches, and loads the chosen unit through the portal.

## The load-path

`~/_arms/arm` is the entry point — the thing that finally *consumes* `_arms`:

```sh
arm find <query…>        # rank capabilities across ALL ecosystems by relevance
arm list [ecosystem]     # the portal index, or one ecosystem's units
arm show <eco> <name>    # LOAD a capability through the portal (prints its body)
arm status               # portal health (verify-portal.sh --check)
```

Example — find a capability without caring which agent owns it, then load it:

```sh
arm find pdf extraction
arm show claude pdf-processing      # ← capability loaded through _arms into context
```

## Why this shape

- **Light**: stdlib-only Python engine + a thin bash dispatcher. No daemon, no
  index file to stale (the index is computed live from the mirror symlinks each
  call), no dependencies. The portal is the source of truth; the router just reads it.
- **Self-referential by design**: `arm find router` finds *this* skill — the
  portal indexes its own first arm. Origination and animation in one unit.
- **Honest about reach**: for Claude-class units, `show` prints the SKILL.md
  (a real context-load). For other agents it prints the unit + the exact invoke
  hint for that agent's own loader — the portal routes you to the door; each
  agent still opens its own.

## Promotion loop (next turn)

A Zone-1 arm that proves itself graduates to the `a-i--skills` distribution and
reflects back through `mirror/source` + `mirror/claude` — at which point Claude's
own Skill tool can load `portal-router` natively, not just via `arm`. That closes
the loop the portal was built to close.
