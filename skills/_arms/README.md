# `/Users/4jp/_arms` — Agent Arms (the skill ecosystem + mirror portal)

**Status:** Seeded 2026-05-23 · Reframed 2026-05-29 as **our** skill ecosystem and a mirror portal over all others. Light, non-git, symlink-driven.

`_arms/` is **our** agent-skill ecosystem — and a **mirror portal** that reflects every *other* agent's skill system into one vantage point. It is deliberately **light on its feet**: it does not copy, vendor, or relocate anything. `skills/` holds our authored work; `mirror/` reflects the rest by live symlink.

```
_arms/
├── README.md     — this file
├── MANIFEST.md   — routing law (what is ours vs what is mirrored)
├── INDEX.md      — thin live index of the portal (regenerated, not hand-maintained)
├── arm           — THE LOAD-PATH: route capability through the portal (find/list/show/status)
├── skills/       — OUR work: operator-authored arms (portal-router = the first)
├── mirror/       — THE PORTAL: live symlinks reflecting every ecosystem (zero copy)
└── .claude/plans/ — plans authored in this scope
```

## Two halves: our work, and the portal

**Our work** lives in `skills/` — operator-authored skills, the arms we forge for this fleet. This is the only place `_arms` *owns* bytes. The first forged arm is **`portal-router`** (`skills/portal-router/`) — the capability `_arms` is uniquely positioned to provide because it alone sees every agent at once: cross-agent capability resolution. See "The load-path" below.

**The portal** lives in `mirror/` — a set of symlinks that reflect, live, the skill (or skill-equivalent) home of every agent system on this machine. A symlink *is* a mirror: it shows current state with zero duplication and never drifts. You `cd _arms/mirror/<agent>` and you are looking straight into that agent's real ecosystem.

## The load-path (`arm`) — what makes `_arms` a *being*, not just a lens

`~/_arms/arm` is the entry point that loads/dispatches capability **through** the portal. Before it existed, `_arms` was inert — a vantage point nothing consumed. `arm` gives it agency: operator or agent now routes through `_arms` to reach any agent's capability (Rule #7 — the loop closes; something finally consumes the portal).

```sh
arm find <query…>        # rank capabilities across ALL ecosystems by relevance
arm list [ecosystem]     # the portal index (computed live from the mirror, never stale)
arm show <eco> <name>    # LOAD one capability through the portal (prints its body)
arm status               # portal health (→ verify-portal.sh --check)
```

The index is computed live each call from the mirror symlinks (no stale index file). It currently spans **1450+ capabilities across 7 ecosystems** — Claude/Codex/Gemini `SKILL.md` dirs, OpenCode flat command `.md`, a-i--skills `*.skill/` dirs — normalized to one record shape by `skills/portal-router/resolve.py` (stdlib-only Python; light). For Claude-class units `show` prints the unit (a real context-load); for other agents it prints the unit plus the exact invoke hint for that agent's own loader — the portal routes you to the door; each agent opens its own.

## The mirror — what reflects what

| Portal link | Reflects | Their capability node | Authority |
|---|---|---|---|
| `mirror/source` | `~/Code/organvm/a-i--skills` | the git repo | **ours** — source-of-truth (remote `a-organvm/a-i--skills`) |
| `mirror/claude` | `~/.claude/skills` → a-i--skills distribution | `skills/` | **ours**, deployed to Claude runtime |
| `mirror/agents` | `~/.agents/skills` | `skills/` | neutral cross-agent pool |
| `mirror/codex` | `~/.codex/skills` | `skills/` | vendor (Codex-native) |
| `mirror/gemini` | `~/.gemini/skills` | `skills/` | vendor (Gemini/GCP) |
| `mirror/opencode-commands` | `~/.config/opencode/commands` | `commands/` (no `skills/`) | vendor (OpenCode) |
| `mirror/openclaw-extensions` | `~/.openclaw/extensions` | `extensions/` (no `skills/`) | vendor (OpenClaw) |
| `mirror/openclaw-agents` | `~/.openclaw/agents` | `agents/` | vendor (OpenClaw) |

Named vacuums (Rule #1 — N/A is never a resting state): **OpenCode** and **OpenClaw** expose no `skills/` node. The portal mirrors their real capability surface (`commands`, `extensions`, `agents`) rather than silently dropping them. If either grows a native `skills/` home later, add `mirror/<agent>` then.

## Design law (the gravitational center)

Derived by cascade — standards → protocol → precedent → ideal form:
- **Single source of truth.** `_arms` never duplicates a distribution. The runtime (`~/.claude/skills`) stays pointed at `a-i--skills`; `_arms` points at the runtime. No forked substrate.
- **Precedent already set it.** `~/.claude/skills` was *already* a symlink into `a-i--skills`. The portal just extends the pattern the runtime proved.
- **Light on its feet — but never local-only.** Symlinks + a thin index + two prose docs. No bulk move, no registry copy. *Light means minimal machinery, not fragile:* the 8 mirror links are chezmoi-tracked as templated `symlink_*.tmpl` source (domus `_arms/mirror/`), so `chezmoi apply --force ~/_arms/mirror` reproduces the entire portal deterministically on any machine. Declared once, restored always — no hand-rebuild ever. Adding/repointing an ecosystem is `ln -sfn <target> mirror/<name>` **then `chezmoi add`** so the change persists.

## Verifying, healing & regenerating

`verify-portal.sh` wraps chezmoi (the source of truth + restore mechanism):

```sh
./verify-portal.sh          # heal from tracked source, check targets, regen INDEX.md
./verify-portal.sh --check  # check only, no mutation; exit 1 if any link MISSING or DANGLING
chezmoi apply --force ~/_arms/mirror   # restore every link from scratch (fresh machine)
```

`INDEX.md` is its output — a thin live snapshot, never hand-maintained (the tracked `symlink_*.tmpl` source is authoritative). **MISSING** = a declared link was deleted (heal restores it); **DANGLING** = a target moved (repoint + `chezmoi add`). `--check` is non-mutating and CI/hook-ready — wire it into a SessionStart hook if you ever want continuous watch; not standing by default (light on its feet).

## Promotion (our skills outward)

A skill authored in `skills/` can graduate to the distribution at `~/Code/organvm/a-i--skills/skills/<category>/<name>.skill/` (then registered in `distributions/skills-registry.json`), which is in turn reflected back here via `mirror/source` and `mirror/claude`. The loop closes on itself.
