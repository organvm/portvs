# `_arms/` MANIFEST — routing law

`_arms/` has exactly two zones. Everything routes to one of them.

## Zone 1 — `skills/` (OUR work; bytes we own)

A skill belongs in `_arms/skills/` when it is:
- **Operator-authored** — written by the user (or by Claude on the user's behalf) for this fleet.
- **Stable enough to invoke** — has a `SKILL.md` with `name` + `description` frontmatter.

Drafts live in `_arms/skills/<name>.draft/` (the `.draft` suffix) until they have a working `SKILL.md`.

## Zone 2 — `mirror/` (THE PORTAL; symlinks, never bytes)

`mirror/` holds **only symlinks** to other ecosystems' real skill (or skill-equivalent) homes. Rules:
- **Never copy bytes into `mirror/`.** If you find a real file or directory there (not a symlink), that is a leak — convert it to a symlink or move it to `skills/`.
- **One `ln -sfn` per ecosystem.** Re-pointing or adding an agent is a single command; deleting a link removes a reflection, never the source.
- **Map to the real capability node.** If an agent has no `skills/`, mirror what it does have (`commands`, `extensions`, `agents`) and name the link accordingly (e.g. `opencode-commands`). Naming the substitute *is* naming the vacuum (Rule #1).

## What does NOT belong in `_arms/` at all

- **Copies of distribution skills** — those live once, at `~/Code/organvm/a-i--skills/`, and are *reflected* via `mirror/source` + `mirror/claude`. Never duplicate them here.
- **One-off transcripts of skill *output*** — those go to plan files, not skills.

## Skill structure (Zone 1)

```
skills/<name>/
├── SKILL.md           ← required, with frontmatter
├── scripts/           ← optional helper scripts
├── references/        ← optional reference docs
└── assets/            ← optional templates/resources
```

```yaml
---
name: <short-kebab-case>
description: <one-line invocation description>
metadata:
  authored: YYYY-MM-DD
  status: draft | active | promoted | deprecated
  promoted_to: <distribution path if promoted>
---
```

## Promotion (Zone 1 → distribution → reflected back)

1. **To distribution** — copy to `~/Code/organvm/a-i--skills/skills/<category>/<name>.skill/`, register in `distributions/skills-registry.json`, then mark the `_arms/` copy `status: promoted` with a `promoted_to:` pointer. It returns to view through `mirror/source` + `mirror/claude` — the loop closes.
2. **To chezmoi-managed personal** — move to the chezmoi `private_dot_claude/skills/<name>/` source; chezmoi deploys it to `~/.claude/skills/<name>/`. Mark the `_arms/` copy `status: promoted`.

Demotion is the reverse — copy a distribution skill back to `_arms/skills/<name>.rework/` and iterate freely.

## Deprecation

A skill marked `status: deprecated` stays on disk ≥90 days before deletion. Move to `_arms/skills/_attic/<name>/` rather than deleting outright. (Applies to Zone 1 only — you cannot deprecate a mirror, only unlink it.)

## Plans

Plans authored while working in `_arms/` land in `_arms/.claude/plans/`. Plans about the portal's structure (adding/removing ecosystems, registry shape) land in `_dot-config/.claude/plans/` (substrate-governance scope).

## Cross-references

- `INDEX.md` — thin live snapshot of the portal (regenerated, not authoritative; the symlinks are).
- Skills registry (`~/Code/organvm/a-i--skills/distributions/skills-registry.json`) — authoritative for *distributed* skills, reflected here via `mirror/source`.
- Process Pillar charter (`_dot-config/.claude/plans/2026-05-23-process-pillar-charter.md`) — Process Pillar members may live in Zone 1.
