# PORTVS — The Reflection Membrane

The unified work graph for the multi-agent ecosystem. Every artifact — memory, plans, governance, registries, conventions — is a node in one graph.

## Protocol

### Publish

Each agent writes durable artifacts to its outbox on closeout:

```
~/.claude/portal-out/session-{date}-{id}.jsonl
~/.codex/portal-out/session-{date}-{id}.jsonl
~/.gemini/portal-out/session-{date}-{id}.jsonl
```

Format: one JSON node per line (JSONL). Each line is a valid node per `graph-schema.json`.

### Aggregate

`portal-sync` reads all outboxes, merges by `id`, and writes the canonical graph:

```
~/_portal/graph.jsonl
```

Merge rules (deterministic):
- Duplicate `id`: latest `modified` timestamp wins.
- Version chain: if node.supersedes points to an existing node, the superseded node's `superseded_by` is set and its `phase` transitions to `retired`.
- Archive: nodes with `phase: retired` older than 90 days move to `archive/graph-YYYY-MM.jsonl`.

### Consume

Each agent reads `~/_portal/graph.jsonl` on SessionStart, filtered by:
- `scope: global` — always visible
- `scope: project:<current-repo-path>` — scoped to the active project
- `phase: accepted|done` — only durable state (exclude drafts and retired)

### Phase Transitions

| From | To | Trigger |
|---|---|---|
| ephemeral | draft | Agent saves work-in-progress to outbox |
| draft | proposed | Agent publishes for review |
| proposed | accepted | Human or primary-domain agent approves |
| accepted | done | Work completed, verified |
| done | retired | Superseded by newer version |
| retired | archive | portal-sync --prune (90+ days) |

Nothing leaves the lattice. Archive is the final resting state.

## Governance

Governance rules are graph nodes with `domain: governance`. They carry `version` for semver evolution. When a rule is disproved or evolved, the old version's `phase` → `retired` and `superseded_by` points to the new version.

## Consumption Pattern

All agents read this file on startup. The human reads it to understand system state. No agent writes to it directly — only `portal-sync` writes the canonical graph.

## Authoritative Copy

This repository (`4444J99/portvs`) is the single source of truth. All other surfaces are projections or caches.
