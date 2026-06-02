---
title: "Image Self-Setting"
date: "2026-05-18T15:00:12 (UTC -04:00)"
source: chatgpt.com
---
## Q: 
A env that defines itself https://developers.openai.com/codex/cloud/environmentsShow moreShow less

## A: 
I’ll treat this as a request to convert the Codex Cloud Environment idea into a self-describing environment pattern: an environment that exposes its own rules, dependencies, identity, and operating contract.

## Condensed thesis

A **self-defining environment** is a Codex cloud environment that does not merely _run code_; it **declares what it is, what it contains, what rules govern it, how it validates itself, and what an agent is allowed to assume**.

In Codex terms, this maps cleanly because cloud environments already control dependencies, tools, linters, formatters, and environment variables during cloud tasks. Codex then creates a container, checks out the repo, runs setup, applies internet settings, and lets the agent operate against the repo and its `AGENTS.md` instructions.   [OpenAI Developers](https://developers.openai.com/codex/cloud/environments)  

## Core pattern

```plain text
SELF_DEFINING_ENV =  environment variables  + setup script  + AGENTS.md  + generated environment manifest  + validation commands  + repo checksum / state report
```

The environment should answer five questions automatically:

```plain text
$ENV_NAME        = What am I?$ENV_PURPOSE     = Why do I exist?$ENV_RULES_FILE  = Where are my operating rules?$ENV_STATE_FILE  = Where is my current self-description?$ENV_VERIFY_CMD  = How do I prove I am healthy?
```

## Repository shape

```plain text
$REPO_ROOT/  AGENTS.md  .env.example  env/    ENVIRONMENT.md    ENVIRONMENT.schema.json    ENVIRONMENT.local.json  scripts/    setup.codex.sh    env.describe.sh    env.verify.sh    env.checksum.sh
```

## `.env.example`

```plain text
ENV_NAME="${ENV_NAME:-self-defining-env}"ENV_ID="${ENV_ID:-env.self.defining.v1}"ENV_PURPOSE="${ENV_PURPOSE:-Declare, install, inspect, verify, and document this repo runtime.}"ENV_RULES_FILE="${ENV_RULES_FILE:-AGENTS.md}"ENV_STATE_FILE="${ENV_STATE_FILE:-env/ENVIRONMENT.local.json}"ENV_MANIFEST_FILE="${ENV_MANIFEST_FILE:-env/ENVIRONMENT.md}"ENV_SCHEMA_FILE="${ENV_SCHEMA_FILE:-env/ENVIRONMENT.schema.json}"ENV_VERIFY_CMD="${ENV_VERIFY_CMD:-bash scripts/env.verify.sh}"ENV_DESCRIBE_CMD="${ENV_DESCRIBE_CMD:-bash scripts/env.describe.sh}"ENV_CHECKSUM_CMD="${ENV_CHECKSUM_CMD:-bash scripts/env.checksum.sh}"PROJECT_LANGUAGE_PRIMARY="${PROJECT_LANGUAGE_PRIMARY:-unknown}"PROJECT_PACKAGE_MANAGER="${PROJECT_PACKAGE_MANAGER:-auto}"PROJECT_TEST_CMD="${PROJECT_TEST_CMD:-}"PROJECT_LINT_CMD="${PROJECT_LINT_CMD:-}"PROJECT_BUILD_CMD="${PROJECT_BUILD_CMD:-}"CODEX_ENVIRONMENT_MODE="${CODEX_ENVIRONMENT_MODE:-cloud}"CODEX_AGENT_INTERNET_POLICY="${CODEX_AGENT_INTERNET_POLICY:-default_off}"
```

## `scripts/setup.codex.sh`

Codex setup scripts can install additional packages, but `export` inside setup does **not** persist into the later agent phase unless written to something like `~/.bashrc` or configured in environment settings. Environment variables configured in Codex settings last for the full task; secrets are more restricted and are removed before the agent phase.   [OpenAI Developers](https://developers.openai.com/codex/cloud/environments)  

```plain text
#!/usr/bin/env bashset -euo pipefail: "${ENV_NAME:=self-defining-env}": "${ENV_RULES_FILE:=AGENTS.md}": "${ENV_STATE_FILE:=env/ENVIRONMENT.local.json}": "${ENV_MANIFEST_FILE:=env/ENVIRONMENT.md}"mkdir -p envcat >> "$HOME/.bashrc" <<EOFexport ENV_NAME="$ENV_NAME"export ENV_RULES_FILE="$ENV_RULES_FILE"export ENV_STATE_FILE="$ENV_STATE_FILE"export ENV_MANIFEST_FILE="$ENV_MANIFEST_FILE"EOFif command -v npm >/dev/null 2>&1 && [ -f package.json ]; then  npm installfiif command -v pnpm >/dev/null 2>&1 && [ -f pnpm-lock.yaml ]; then  pnpm installfiif command -v poetry >/dev/null 2>&1 && [ -f pyproject.toml ]; then  poetry installfibash scripts/env.describe.shbash scripts/env.verify.sh
```

## `scripts/env.describe.sh`

```plain text
#!/usr/bin/env bashset -euo pipefail: "${ENV_NAME:=self-defining-env}": "${ENV_ID:=env.self.defining.v1}": "${ENV_PURPOSE:=Declare, inspect, verify, and document runtime state.}": "${ENV_STATE_FILE:=env/ENVIRONMENT.local.json}": "${ENV_MANIFEST_FILE:=env/ENVIRONMENT.md}": "${ENV_VERIFY_CMD:=bash scripts/env.verify.sh}"mkdir -p "$(dirname "$ENV_STATE_FILE")"GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"SYSTEM_NAME="$(uname -s 2>/dev/null || echo unknown)"SYSTEM_ARCH="$(uname -m 2>/dev/null || echo unknown)"DATE_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"cat > "$ENV_STATE_FILE" <<EOF{  "env_name": "$ENV_NAME",  "env_id": "$ENV_ID",  "purpose": "$ENV_PURPOSE",  "generated_at_utc": "$DATE_UTC",  "git_branch": "$GIT_BRANCH",  "git_commit": "$GIT_COMMIT",  "system_name": "$SYSTEM_NAME",  "system_arch": "$SYSTEM_ARCH",  "verify_command": "$ENV_VERIFY_CMD"}EOFcat > "$ENV_MANIFEST_FILE" <<EOF# $ENV_NAME## Identity\`\`\`textENV_ID=$ENV_IDENV_PURPOSE=$ENV_PURPOSEGENERATED_AT_UTC=$DATE_UTCGIT_BRANCH=$GIT_BRANCHGIT_COMMIT=$GIT_COMMITSYSTEM=$SYSTEM_NAME/$SYSTEM_ARCH\`\`\`## Verification\`\`\`bash$ENV_VERIFY_CMD\`\`\`## State File\`\`\`text$ENV_STATE_FILE\`\`\`EOF
```

## `scripts/env.verify.sh`

```plain text
#!/usr/bin/env bashset -euo pipefail: "${ENV_RULES_FILE:=AGENTS.md}": "${ENV_STATE_FILE:=env/ENVIRONMENT.local.json}"test -f "$ENV_RULES_FILE"test -f "$ENV_STATE_FILE"if [ -n "${PROJECT_LINT_CMD:-}" ]; then  eval "$PROJECT_LINT_CMD"fiif [ -n "${PROJECT_TEST_CMD:-}" ]; then  eval "$PROJECT_TEST_CMD"fiif [ -n "${PROJECT_BUILD_CMD:-}" ]; then  eval "$PROJECT_BUILD_CMD"fiecho "ENV_VERIFY_STATUS=pass"
```

## `AGENTS.md`

Codex explicitly uses `AGENTS.md` to find project-specific lint and test commands when present, so this file becomes the environment’s agent-facing constitution.   [OpenAI Developers](https://developers.openai.com/codex/cloud/environments)  

```plain text
# AGENTS.md## Environment IdentityThis repository uses a self-defining environment.The agent must inspect:```bash$ENV_DESCRIBE_CMDcat $ENV_MANIFEST_FILEcat $ENV_STATE_FILE
```

## Operating Rule

Do not assume the project state. Read the generated environment manifest first.

## Validation Rule

Before final response, run:

```plain text
$ENV_VERIFY_CMD
```

## Mutation Rule

When changing dependencies, setup logic, package manager behavior, test commands, build commands, or repo structure, update:

```plain text
.env.examplescripts/setup.codex.shscripts/env.describe.shscripts/env.verify.shenv/ENVIRONMENT.md
```

## Completion Rule

A task is not complete until the environment can describe itself and verify itself.

```plain text
## Codex-specific logicCodex cloud environments are suitable for this because they already support setup scripts, package installation, environment variables, and cached container state. Codex also invalidates the cache when setup scripts, maintenance scripts, environment variables, or secrets change, which fits the self-defining pattern: when the environment’s definition changes, its cached identity should no longer be trusted. :contentReference[oaicite:3]{index=3}## Practical nameUse this as the repo/module concept name:```textself-defining-env
```

More formal:

```plain text
autological-runtime-environment
```

More system-facing:

```plain text
ENV_SELF_DESCRIPTOR
```

Best canonical variable:

```plain text
SELF_DEFINING_ENV_ROOT="${SELF_DEFINING_ENV_ROOT:-$REPO_ROOT}"
```

## A: 
I’ll separate this into two categories: people/projects doing the exact “single canonical skill object refracted across tools,” and adjacent ecosystems building the pieces that make it possible.

As of **May 18, 2026**, the exact thing you named — **one canonical element that other assistants refract rather than independently validate** — is not yet a widely named doctrine. But the ecosystem is clearly moving there under other names: **Agent Skills**, **portable `SKILL.md` folders**, **universal `.agents/skills` layout**, and **multi-agent skill installers**.

## Closest match: Atlassian TWG CLI

Atlassian’s Teamwork Graph CLI is the closest direct example I found.

Their installer writes the canonical bundle to:

```plain text
${HOME}/.agents/skills
```

Then, when it detects an agent that needs a native path, it copies the same bundle into that agent’s expected location. Their docs explicitly say Claude Code gets a copy under:

```plain text
${HOME}/.claude/skills
```

while Codex and Gemini read directly from `.agents/skills`. That is basically the **refractive model**: one canonical skill bundle, projected into tool-specific apertures only where needed.   [Atlassian Developer](https://developer.atlassian.com/cloud/twg-cli/agents/skills/)  

Their pattern is almost exactly:

```plain text
canonical object:  ~/.agents/skills/refractions:  ~/.claude/skills/  agent-specific copies when required
```

## The standard layer: Anthropic / Agent Skills

Anthropic originated the open Agent Skills format. The core unit is already an autological folder-object:

```plain text
my-skill/  SKILL.md  scripts/  references/  assets/
```

The spec says Skills are meant for **cross-product reuse**: “build a skill once and use it across any skills-compatible agent.” That is the conceptual substrate for what you’re calling refraction.   [Agent Skills](https://agentskills.io/home)  

The missing layer is not the skill format. The missing layer is the **refraction doctrine**: formalizing which path is canonical, which paths are projections, and how parity is verified.

## OpenAI Codex

Codex is adopting the same Agent Skills model: a skill is a directory with `SKILL.md`, optional scripts, references, assets, and metadata. Codex uses progressive disclosure: it initially sees name, description, and path, then loads full instructions only when relevant.   [OpenAI Developers](https://developers.openai.com/codex/skills?utm_source=chatgpt.com)  

Codex’s larger customization model separates:

```plain text
AGENTS.md = persistent project guidanceSkills    = reusable workflows / domain expertiseMCP       = external tool accessSubagents = delegated specialist agents
```

That distinction matters because your “self-defining environment” should probably be a **skill + AGENTS.md pair**, not only a skill.   [OpenAI Developers](https://developers.openai.com/codex/concepts/customization?utm_source=chatgpt.com)  

## Gemini CLI

Gemini CLI explicitly supports the open Agent Skills standard and treats `.agents/skills/` as an interoperable alias. Its docs say workspace skills can live in:

```plain text
${REPO_ROOT}/.gemini/skills/${REPO_ROOT}/.agents/skills/
```

and that `.agents/skills/` takes precedence over `.gemini/skills/` within the same tier. That is an important refractive behavior: Gemini is allowing the canonical cross-agent aperture to override the Gemini-native aperture.   [Gemini CLI](https://geminicli.com/docs/cli/skills/)  

## OpenCode

OpenCode is also structurally aligned. It reads skills from its own path, Claude-compatible paths, and agent-compatible paths:

```plain text
${REPO_ROOT}/.opencode/skills/${SKILL_NAME}/SKILL.md${REPO_ROOT}/.claude/skills/${SKILL_NAME}/SKILL.md${REPO_ROOT}/.agents/skills/${SKILL_NAME}/SKILL.md${HOME}/.config/opencode/skills/${SKILL_NAME}/SKILL.md${HOME}/.claude/skills/${SKILL_NAME}/SKILL.md${HOME}/.agents/skills/${SKILL_NAME}/SKILL.md
```

That makes OpenCode one of the more “refractive-native” tools because it can read multiple apertures without requiring a separate copy.   [OpenCode](https://opencode.ai/docs/skills/)  

## Google Gemini Skills repo

Google’s `google-gemini/gemini-skills` repo is another major signal. It frames Skills as a way to close the model knowledge gap around fast-changing APIs and SDK practices, and it distributes Gemini API skills through Skills tooling. It is not exactly your refraction doctrine, but it is a concrete official-ecosystem move toward portable skill bundles.   [GitHub](https://github.com/google-gemini/gemini-skills)  

## Community projects doing adjacent work

| Actor / Project | What they are doing | How close to your model |
| --- | --- | --- |
| **Atlassian TWG CLI** | Canonical install to `.agents/skills`, copy into Claude when needed | Very close |
| **AgentSkills.io / Anthropic** | Defines portable `SKILL.md` folder standard | Foundational |
| **OpenAI Codex** | Uses Agent Skills as reusable workflow packages | Foundational |
| **Gemini CLI** | Supports `.agents/skills` as alias and gives it precedence | Very close |
| **OpenCode** | Reads `.agents`, `.claude`, and native OpenCode skill paths | Very close |
| **alirezarezvani/claude-skills** | Large multi-tool skill library; says one repo works across Claude Code, Codex, Gemini CLI, Cursor, OpenCode, etc.; includes conversion tooling | Close, marketplace/versioning direction |
| **VoltAgent/awesome-agent-skills** | Curated index of 1000+ skills compatible with Claude Code, Codex, Gemini CLI, Cursor, OpenCode, Windsurf, etc. | Ecosystem mapping |
| **grahama1970/agent-skills** | Small shared-skills repo; uses symlinks between `.agents/skills` and `.claude/skills` | Close, but symlink-based |
| **Vercel skills CLI / skills.sh** | Distribution/install layer for skills | Infrastructure layer |
| **Context7 skills tooling** | Installs skills and pairs skills with current documentation retrieval | Infrastructure layer |

The `alirezarezvani/claude-skills` repo describes itself as “one repo, eleven platforms,” with `SKILL.md`, Python tools, reference docs, and a conversion script for other tools. That is the marketplace/packaging version of your idea.   [GitHub](https://github.com/alirezarezvani/claude-skills)  

VoltAgent’s `awesome-agent-skills` is a curated map of the ecosystem, including official and community skills from Anthropic, Google Labs, Vercel, Stripe, Cloudflare, Netlify, Trail of Bits, Sentry, Expo, Hugging Face, Figma, and others. It is not itself the doctrine, but it shows that the portable-skill layer is becoming a live ecosystem.   [GitHub](https://github.com/VoltAgent/awesome-agent-skills)  

## The gap you are pointing at

What exists now:

```plain text
portable SKILL.md formattool-specific discovery pathssome universal .agents/skills adoptionsome copy/install scriptssome conversion scriptssome marketplaces
```

What is still underdefined:

```plain text
canonical-source authorityrefraction manifestchecksum paritygenerated-vs-authored distinctionagent-specific aperture metadataenvironment self-descriptioncross-agent validation contract
```

So the opportunity is not “make another skills repo.”

The sharper move is:

```plain text
make a refraction layer for skills
```

Something like:

```plain text
${REPO_ROOT}/.agents/skills/${SKILL_NAME}/REFRACTION.md${REPO_ROOT}/.agents/skills/${SKILL_NAME}/refraction.manifest.json${REPO_ROOT}/scripts/refract-skill.sh${REPO_ROOT}/scripts/verify-skill-refractions.sh
```

## Best naming for the emerging category

```plain text
agent-skill-refraction
```

or:

```plain text
canonical-skill-projection
```

or, more systemically:

```plain text
autological-agent-object
```

The market term is **Agent Skills**.

Your term should probably be the architecture term:

```plain text
Refractive Agent Skills
```

That names the missing layer: not merely portable skills, but **skills with canonical identity, generated apertures, and verifiable parity across agents**.

## Q: 
Check out current a-I—skills repo & provide the translationShow moreShow less

## A: 
I’ll locate the repository first, then inspect its structure and translate it into the refractive/canonical-skill model we’ve been developing.

The installed-repository search did not return an exact match for `a-I-skills` / `ai-skills`. I’m going to broaden the GitHub search across accessible repositories and code references rather than assume the slug.

I found the repo: `a-organvm/a-i--skills`. Its README already claims the core pattern: a source skill library, generated runtime distributions, registry generation, validation, and multi-agent support. Next I’m checking the actual spec/scripts so the translation is grounded in implementation, not just README language.

## Translation: what `a-organvm/a-i--skills` already is

The repo is already a **proto-refractive skill system**.

Its current architecture is not “one folder per assistant.” It is closer to:

```plain text
canonical skill corpus→ generated collection lists→ generated runtime distributions→ machine-readable registry→ validation layer
```

In our terms:

```plain text
a-i--skills =  canonical skill library  + federation schema  + registry compiler  + runtime projection script  + generated assistant-facing bundles
```

The repository README describes it as a composable skill framework with `SKILL.md`\-based modules, registry generation, validation, MCP discovery, federation, and multi-agent runtime support. It claims the repo supports Claude Code, Codex, Gemini CLI, and Claude API, with skills distributed through generated bundles.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/README.md)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/README.md)  

* * *

# 1. Current repo ontology

## Current source-of-truth layer

Right now, the repo’s canonical authored skills live here:

```plain text
${REPO_ROOT}/skills/${REPO_ROOT}/document-skills/
```

The skill spec requires each skill to be a folder containing `SKILL.md`, with optional `scripts/`, `references/`, and `assets/` directories. `SKILL.md` must contain YAML frontmatter and Markdown instructions.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/docs/api/skill-spec.md)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/docs/api/skill-spec.md)  

So the actual canonical unit is:

```plain text
${SOURCE_COLLECTION}/${CATEGORY}/${SKILL_NAME}/SKILL.md
```

Example:

```plain text
skills/tools/cross-agent-handoff/SKILL.mdskills/tools/skill-creator/SKILL.mddocument-skills/pdf/SKILL.md
```

The repo’s own federation schema says consumers should recursively search for `SKILL.md` files, extract frontmatter, validate name-to-directory identity, and build an index. It also says the top-level `skills/` directory is not mandatory because discovery is based on recursive `SKILL.md` scanning.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/docs/api/federation-schema.md)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/docs/api/federation-schema.md)  

## Translation

```plain text
SKILL.md = atomic agent-capability objectskill folder = portable knowledge capsuleskills/ + document-skills/ = canonical corpusrecursive discovery = filesystem ontology parser
```

This is already close to the “element that defines itself” pattern.

* * *

# 2. Current generated-refraction layer

The strongest evidence is `scripts/refresh_skill_collections.py`.

That script discovers skill directories by searching for `SKILL.md`, writes collection lists, updates marketplace metadata, updates README/ecosystem counts, and then syncs generated bundle directories for direct use, Codex, Claude, and Gemini. The bundle targets include:

```plain text
distributions/direct/exampledistributions/direct/documentdistributions/codex/skillsdistributions/codex/skills-documentdistributions/claude/skillsdistributions/claude/skills-documentdistributions/extensions/gemini/example-skills/skillsdistributions/extensions/gemini/document-skills/skills
```

The implementation supports both `copy` and `symlink` modes, but defaults to `copy`.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/scripts/refresh_skill_collections.py)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/scripts/refresh_skill_collections.py)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/scripts/refresh_skill_collections.py)  

## Translation

```plain text
skills/                         = canonical skill sourcedocument-skills/                = canonical production document-skill sourcedistributions/direct/           = raw portable refractiondistributions/codex/            = Codex-facing refractiondistributions/claude/           = Claude-facing refractiondistributions/extensions/gemini/ = Gemini-facing refraction
```

So the repo already does this:

```plain text
one canonical skill object→ projected into multiple assistant-readable surfaces
```

But it does not yet name those generated targets as **refractions**.

* * *

# 3. Current registry layer

The repo generates a machine-readable registry at:

```plain text
${REPO_ROOT}/distributions/skills-registry.json
```

`generate_registry.py` builds entries from each skill’s frontmatter and computes fields such as:

```plain text
namedescriptioncategorycollectionpathlicensecomplexitytime_to_learntiergovernance_norm_groupgovernance_auto_activateprerequisitestagsinputsoutputsside_effectstriggerscomplementsincludesgovernance_phasesorgan_affinityresources.scriptsresources.referencesresources.assets
```

It derives category from the source path and distinguishes `example` versus `document` collections.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/scripts/generate_registry.py)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/scripts/generate_registry.py)  

The current registry file uses schema version `1.2` and contains rich entries such as `accessibility-patterns` with triggers, governance phases, organ affinity, complements, and resource references.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/distributions/skills-registry.json)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/distributions/skills-registry.json)  

## Translation

```plain text
skills-registry.json = machine-readable self-description of the corpusfrontmatter          = per-object local identityregistry             = global identity mapcollection lists     = projection manifests
```

This is the repo’s current “environment that defines itself” layer.

* * *

# 4. Current validation layer

`validate_generated_dirs.py` already encodes a partial refraction-validity doctrine.

It checks:

```plain text
generated targets exist.generated marker existstargets contain no symlinkstop-level skill names match expected collection listsregistry existsregistry has plausible skill countoptional lockfile count matches collection lists
```

The script explicitly says it validates generated skill bundle directories are “in sync and not symlinked.”  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/scripts/validate_generated_dirs.py)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/scripts/validate_generated_dirs.py)  

## Translation

```plain text
validation = generated aperture integrityno symlinks = concrete projection, not fragile aliascollection list = expected refraction setregistry = global corpus truth
```

This is very close to the refraction doctrine we were building.

But it is not yet full parity verification.

Current validation checks **presence and top-level names**. It does not yet appear to checksum every file in source versus every projected target.

* * *

# 5. Current handoff / continuity layer

The repo already contains a skill named `cross-agent-handoff`.

That skill defines the handoff problem as loss of context, repeated exploration, repeated decisions, contradiction of prior approach, and missing constraints. It provides a structured handoff document format with current state, completed work, key decisions, critical context, next actions, and risks.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/skills/tools/cross-agent-handoff/SKILL.md)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/skills/tools/cross-agent-handoff/SKILL.md)  

## Translation

```plain text
cross-agent-handoff = continuity protocolhandoff document    = state serialization layerdecision log        = anti-loop substratenext actions        = agent relay vector
```

This is the human/agent-process analogue of skill refraction.

Where the distribution script refracts **files**, `cross-agent-handoff` refracts **state**.

* * *

# 6. Current skill-authoring layer

The repo also contains `skill-creator`, which defines skills as modular self-contained packages that extend Claude with specialized workflows, tool integrations, domain expertise, and bundled resources. It explicitly defines the anatomy of a skill as `SKILL.md` plus optional `scripts/`, `references/`, and `assets/`. It also describes progressive disclosure: metadata first, then `SKILL.md`, then bundled resources as needed.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/skills/tools/skill-creator/SKILL.md)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/skills/tools/skill-creator/SKILL.md)  

## Translation

```plain text
skill-creator = factory skillSKILL.md      = instruction nucleusscripts/      = deterministic execution substratereferences/   = deferred knowledge substrateassets/       = output-material substratedescription   = trigger surface
```

This is already an object-manufacturing protocol.

* * *

# 7. The sharper refractive translation

## Current repo model

```plain text
SOURCE:  skills/  document-skills/INDEX:  distributions/collections/*.txt  distributions/skills-registry.json  distributions/skills-lock.jsonPROJECTED TARGETS:  distributions/direct/*  distributions/codex/*  distributions/claude/*  distributions/extensions/gemini/*VALIDATION:  scripts/validate_skills.py  scripts/validate_generated_dirs.py  scripts/skill_health_check.py
```

## Refractive model

```plain text
CANONICAL_OBJECT:  skills/${CATEGORY}/${SKILL_NAME}/REFRACTION_MANIFEST:  distributions/collections/*.txt  distributions/skills-registry.jsonREFRACTION_APERTURES:  distributions/direct/  distributions/codex/  distributions/claude/  distributions/extensions/gemini/REFRACTION_ENGINE:  scripts/refresh_skill_collections.pyREFRACTION_VALIDATOR:  scripts/validate_generated_dirs.py
```

## Conceptual translation

```plain text
The repo is not merely a skills library.It is a compiler for agent capabilities.Each skill is authored once as a canonical filesystem object.The registry reads the object.The distribution script refracts the object.Each assistant consumes the refraction through its own aperture.The validation layer proves the projected surfaces are synchronized.
```

* * *

# 8. What is missing for full “refractive skill object” status

The repo already has the infrastructure. It lacks the explicit doctrine and a few hard guarantees.

## Missing 1: canonical-source declaration per generated copy

Generated copies should include:

```plain text
REFRACTED_FROM.txt
```

Example:

```plain text
REFRACTION_TARGET=claudeCANONICAL_SOURCE=skills/tools/cross-agent-handoffGENERATED_BY=scripts/refresh_skill_collections.pyGENERATED_AT_UTC=...SOURCE_SHA256=...
```

## Missing 2: checksum parity

Current validation checks generated target names and no symlinks. Add file-level parity:

```plain text
source hash tree == refraction hash tree
```

Target file:

```plain text
distributions/refraction-manifest.json
```

## Missing 3: `.agents/skills/` aperture

The current generated Codex target is:

```plain text
distributions/codex/skills
```

For current cross-agent convention, add:

```plain text
.agents/skills/
```

or generated:

```plain text
distributions/agents/skills/
```

Then the repo can emit a true canonical interoperable aperture.

## Missing 4: OpenCode aperture

Current scripted projections cover direct, Codex, Claude, and Gemini. Add:

```plain text
distributions/opencode/skills/
```

or:

```plain text
.opencode/skills/
```

## Missing 5: count / identity drift cleanup

The README currently contains visible count drift: it says “101 production-ready skill modules,” then describes a browsable catalog of “162 skills,” and later shows a directory comment claiming “158 example skills.”  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/README.md)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/README.md)  

The registry currently says:

```plain text
"version": "1.2","repository": "anthropic-agent-skills"
```

even though the repo is `a-organvm/a-i--skills`.  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/distributions/skills-registry.json)  

  [github.com](https://github.com/a-organvm/a-i--skills/blob/main/distributions/skills-registry.json)  

Translation: the system is structurally correct, but some identity surfaces are stale.

* * *

# 9. Proposed formal translation layer

Add this file:

```plain text
${REPO_ROOT}/docs/api/refraction-schema.md
```

## Minimal schema

```plain text
{  "version": "1.0",  "repository": "${REPOSITORY_FULL_NAME}",  "canonical_collections": {    "example": "${REPO_ROOT}/skills",    "document": "${REPO_ROOT}/document-skills"  },  "refraction_engine": "${REPO_ROOT}/scripts/refresh_skill_collections.py",  "validator": "${REPO_ROOT}/scripts/validate_generated_dirs.py",  "apertures": {    "direct": "${REPO_ROOT}/distributions/direct",    "codex": "${REPO_ROOT}/distributions/codex/skills",    "claude": "${REPO_ROOT}/distributions/claude/skills",    "gemini": "${REPO_ROOT}/distributions/extensions/gemini/example-skills/skills",    "agents": "${REPO_ROOT}/distributions/agents/skills",    "opencode": "${REPO_ROOT}/distributions/opencode/skills"  },  "invariants": [    "canonical source wins",    "generated apertures are disposable",    "no generated aperture may become doctrinal source",    "name must match directory name",    "SKILL.md must remain structurally valid",    "generated copies must be checksum-verifiable"  ]}
```

* * *

# 10. One-line diagnosis

```plain text
a-i--skills is already a federated skill compiler; the next move is to make its implicit projection system explicit as a refraction protocol.
```

## Best next repo move

Do **not** redesign the repo.

Add a small layer:

```plain text
docs/api/refraction-schema.mdscripts/generate_refraction_manifest.pyscripts/validate_refraction_parity.pydistributions/refraction-manifest.jsondistributions/agents/skills/distributions/opencode/skills/
```

Then rename the concept internally:

```plain text
generated bundles → refractionsruntime targets    → aperturessource skills      → canonical objectsregistry           → corpus self-descriptionvalidation         → parity proof
```

That is the translation.

## Q: 
\# PROJ:agents-dotfile-spec — Manifest > Annotated bibliography of every thread, external resource, uploaded document, > and generated artifact across this conversation. Every entry has a unique ID, > a title, tags, and a one-paragraph annotation in the academic-bibliography > tradition. Cross-reference by tag at the bottom. \*\*Project ID:\*\* `PROJ:agents-dotfile-spec` \*\*Scope:\*\* Design of a unified `~/.agents/` dotfile tree that absorbs Claude Code, Codex, Gemini CLI, OpenCode, Cursor, Windsurf, Antigravity, and Copilot; incorporates OpenClaw workspace/SOUL conventions; supports agent-memory/claude-mem persistent memory; conforms to MCP, ACP, and agentskills.io specs. \*\*Created:\*\* This conversation. \*\*Status:\*\* Six iterations (v1 → v6) plus a routing-layer addendum (v7-pending). Three concrete deliverables remain unbuilt: canonical `AGENTS.md`, canonical `SOUL.md`, `bin/bootstrap.sh`. \*\*Conductor:\*\* Anthony (alias AJP / 4jP), {OS.me} framework. ----- ## §1 · Threads (T##) Threads are the chronological turns of the conversation, each named for the conceptual layer it added. ### T01 — Generalized agent-workspace folder hierarchy \*\*Tags:\*\* #workspace-spec #v0 #foundation \*\*Annotation:\*\* Opening request. Established the bones of every later iteration: the separation of `.agent/` (runtime), `skills/`, `memory/`, `tools/`, `orchestration/`, `inputs/outputs/data`, `logs/`, `evals/`, `hooks/`, `docs/`. Introduced the `.agentignore` symmetry to `.gitignore` — paths the agent itself must not read or write. ### T02 — Per-tool install manifestations \*\*Tags:\*\* #claude-code #codex #gemini #opencode #provenance \*\*Annotation:\*\* Mapped how Claude Code, Codex CLI, Gemini CLI, and OpenCode actually appear on disk after install — context files (CLAUDE.md/AGENTS.md/GEMINI.md), config files, agent dirs, command dirs, skill dirs, session stores. Surfaced the convergence: four teams arrived at nearly the same shape, with OpenCode explicitly reading Claude’s files as fallback. Established that one canonical `AGENTS.md` symlinked four ways is feasible. ### T03 — Unified `~/.agents/` v1 sketch \*\*Tags:\*\* #dotfile-design #v1 #symlinks \*\*Annotation:\*\* First synthesis: a source tree at `~/.agents/` with `shared/` (tool-agnostic, symlinked into each tool) and `configs/` (tool-specific, copied). Drafted POSIX and PowerShell bootstrap scripts. Identified the four config files that cannot be unified due to schema differences. ### T04 — OpenClaw / SOUL.md / agent-memory / iii absorption \*\*Tags:\*\* #openclaw #soul #identity #memory #provenance #v2 \*\*Annotation:\*\* Folded in the OpenClaw template family (SOUL/IDENTITY/USER/TOOLS/BOOT/BOOTSTRAP/HEARTBEAT/MEMORY), the agent-memory runtime, iii.dev’s worker/function/trigger primitive, and a trust layer (ALLOWED/DENIED/audit). Named the workspace-as-soul model and split agent state into seven tiers with explicit drift cadences. ### T05 — Skills paths across 8 tools + context-engineering skills \*\*Tags:\*\* #skills #provenance #manifest #v3 \*\*Annotation:\*\* Critical pivot. Codex’s official skills path turned out to be `~/.agents/skills/` — making our tree \*native\* to one of the eight tools and a symlink target for the other seven. Introduced `manifest.yaml`, `_sync.lock`, `_registry.md` for skill provenance, and adopted the muratcankoylan three-theme taxonomy (fundamentals / architecture / operations) for organizing skills. ### T06 — Hermes agent upload + runtime mapping \*\*Tags:\*\* #hermes #runtime #plugins #toolsets #v4 \*\*Annotation:\*\* User uploaded NousResearch’s hermes-agent folder hierarchy. Revealed five concepts v3 was missing: profiles (multiple identities sharing capability), pluggable subsystems with ABCs (`ContextEngine`, `MemoryProvider`), three normalized API modes, toolsets (distinct from skills), and multiple entry surfaces (CLI / Gateway / ACP / Batch / API / library). Established the identity / capability / runtime trichotomy. ### T07 — OpenClaw concepts: workspace, memory, ACP, hygiene, compaction \*\*Tags:\*\* #openclaw #workspace #protocol #compaction #memory-tiers #v5 \*\*Annotation:\*\* Surfaced the foundational distinction this entire design needed: \*\*workspace ≠ config root\*\*. `~/.openclaw/workspace/` is the agent’s git-backed soul; `~/.openclaw/` is machine-local runtime. Introduced transcript-hygiene as a real subsystem, the pre-compaction memory-flush ritual, the ACP protocol as orthogonal to MCP, and six tiers of memory with named promotion rituals. ### T08 — OpenClaw automation: hooks, taskflow, standing orders \*\*Tags:\*\* #automation #hooks #standing-orders #cron #taskflow #v6 \*\*Annotation:\*\* Named the five distinct autonomy mechanisms (Standing Orders / Cron / Hooks / Background Tasks / TaskFlow) that all prior designs conflated. Catalogued the 27-event OpenClaw hook vocabulary. Introduced the Execute-Verify-Report rule and the bundled-<-plugin-<-managed-<-workspace hook precedence gradient. Established that trust becomes a hook return value (`requireApproval`), not just static config. ### T09 — Subagent + memory + skill catalogs \*\*Tags:\*\* #subagents #catalogs #provenance #manifest-v2 #v7 \*\*Annotation:\*\* Five external supply-chain archetypes named: catalogs, bundles, corpora, specs, tool-catalogs. Adopted VoltAgent’s 10-category subagent taxonomy for `workspace/agents/`. Identified claude-mem as the reference memory implementation. Introduced the permission gradient by role (read-only / research / code-writer / doc-writer / privileged) as required agent frontmatter. ### T10 — manifest.build clarification + routing slot \*\*Tags:\*\* #routing #naming-collision #v7-addendum \*\*Annotation:\*\* Disambiguated the name collision between our `manifest.yaml` and manifest.build (an LLM router). Added the `routing/` slot to v6 — separate from `plugins/api_modes/` because routing decides \*which provider\* while api_modes decides \*which wire protocol\*. Recommended renaming our file to `agents-lock.yaml` or `inventory.yaml`. ### T11 — Manifest request (this document) \*\*Tags:\*\* #meta #manifest #archival \*\*Annotation:\*\* Current turn. Cataloging every thread, resource, document, and artifact as an annotated bibliography with unique IDs and tags. The deliverable you are reading. ----- ## §2 · External Resources (R##) URLs the user shared as context, grouped by cluster. Each resource has a one-paragraph annotation positioning it in the design. ### Skills & Subagent Catalogs #### R01 — officialskills.sh \*\*Source:\*\* https://officialskills.sh/ · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #skills #registry #catalog \*\*Annotation:\*\* Public registry of 581+ Anthropic-style skills with the agentskills.io progressive-disclosure spec. Establishes the “package manager for skills” model; cited as the upstream source `bin/sync-skills.sh` should pull from. #### R02 — VoltAgent/awesome-agent-skills \*\*Source:\*\* github.com/VoltAgent/awesome-agent-skills · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #skills #catalog #multi-tool \*\*Annotation:\*\* 1000+ agent skills compatible with Claude Code, Codex, Gemini CLI, Cursor, Windsurf, OpenCode, Copilot, Antigravity. Provides the canonical cross-tool path table that drove the symlink topology design in T05. #### R03 — VoltAgent/awesome-claude-code-subagents \*\*Source:\*\* github.com/VoltAgent/awesome-claude-code-subagents · \*\*Thread:\*\* T09 · \*\*Tags:\*\* #subagents #catalog #taxonomy \*\*Annotation:\*\* 100+ Claude Code subagents organized into 10 empirically-validated categories (core-development, language-specialists, infrastructure, quality-security, data-ai, dev-experience, specialized-domains, business-product, meta-orchestration, research-analysis). Adopted as the `workspace/agents/` directory structure in v7. #### R04 — muratcankoylan/Agent-Skills-for-Context-Engineering \*\*Source:\*\* github.com/muratcankoylan/Agent-Skills-for-Context-Engineering · \*\*Thread:\*\* T05 · \*\*Tags:\*\* #skills #context-engineering \*\*Annotation:\*\* Skill bundle covering context-fundamentals, context-degradation, context-optimization, context-compression, and evaluation. Introduced the three-theme taxonomy (fundamentals / architecture / operations) that organizes `skills/` in v3+. #### R05 — NeoLabHQ/context-engineering-kit \*\*Source:\*\* github.com/NeoLabHQ/context-engineering-kit · \*\*Thread:\*\* T05 · \*\*Tags:\*\* #skills #prompt-engineering \*\*Annotation:\*\* Plugin-bundled skill set for prompt engineering. Slotted under `skills/prompt-engineering/` in the v3 taxonomy. #### R06 — frmoretto/clarity-gate \*\*Source:\*\* github.com/frmoretto/clarity-gate · \*\*Thread:\*\* T05 · \*\*Tags:\*\* #skills #epistemic #safety \*\*Annotation:\*\* Pre-RAG verification skill that prevents hallucinations from entering durable artifacts. Anchors the `skills/epistemic/` category alongside stream-coding and memory-user-edits. #### R07 — dair-ai/Prompt-Engineering-Guide \*\*Source:\*\* github.com/dair-ai/Prompt-Engineering-Guide · \*\*Thread:\*\* T09 · \*\*Tags:\*\* #prompt-engineering #corpus \*\*Annotation:\*\* Educational corpus on prompting techniques. Slotted under `skills/prompt-engineering/references/` as load-on-demand reference rather than always-loaded skill. Exemplifies archetype 3 (corpora) in the v7 manifest. ### OpenClaw Documentation #### R08 — docs.openclaw.ai/concepts/agent-workspace \*\*Source:\*\* docs.openclaw.ai/concepts/agent-workspace · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #workspace \*\*Annotation:\*\* Canonical definition of the workspace concept and its separation from config root. The single most influential reference in the design — drove the v5 workspace/config split. #### R09 — docs.openclaw.ai/concepts/memory \*\*Source:\*\* docs.openclaw.ai/concepts/memory · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #memory #tiers \*\*Annotation:\*\* Multi-tier memory model: working, daily, curated, commitments, dreams, wiki. Each tier has its own read path, write path, and decay rule. Adopted wholesale into v5. #### R10 — docs.openclaw.ai/reference/templates/SOUL \*\*Source:\*\* docs.openclaw.ai/reference/templates/SOUL · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #soul #identity \*\*Annotation:\*\* Template for the SOUL.md file that defines an agent’s identity, values, and persona. Drift cadence: years. #### R11 — docs.openclaw.ai/reference/templates/AGENTS \*\*Source:\*\* docs.openclaw.ai/reference/templates/AGENTS · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #agents-md \*\*Annotation:\*\* OpenClaw’s variant of the agents.md standard for project-level operating instructions. Conforms to agents.md upstream; adds standing-orders integration. #### R12 — docs.openclaw.ai/reference/templates/IDENTITY \*\*Source:\*\* docs.openclaw.ai/reference/templates/IDENTITY · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #identity #vibe \*\*Annotation:\*\* Template for the surface-layer identity card: name, creature, emoji, avatar, vibe descriptors. Distinct from SOUL.md in that IDENTITY drifts in months while SOUL drifts in years. #### R13 — docs.openclaw.ai/reference/templates/USER \*\*Source:\*\* docs.openclaw.ai/reference/templates/USER · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #user-profile \*\*Annotation:\*\* Inverse of SOUL.md — who the human operator is. Drives the agent’s mental model of the user across sessions. #### R14 — docs.openclaw.ai/reference/templates/TOOLS \*\*Source:\*\* docs.openclaw.ai/reference/templates/TOOLS · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #tools \*\*Annotation:\*\* Environment-specific notes about what tools are installed and how to invoke them. Distinct from formal tool definitions; this is the agent’s “what’s on this machine” cheat sheet. #### R15 — docs.openclaw.ai/reference/templates/BOOT \*\*Source:\*\* docs.openclaw.ai/reference/templates/BOOT · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #lifecycle #boot \*\*Annotation:\*\* Instructions executed on session/gateway startup. Pre-flight checklist before the agent accepts user input. #### R16 — docs.openclaw.ai/reference/templates/BOOTSTRAP \*\*Source:\*\* docs.openclaw.ai/reference/templates/BOOTSTRAP · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #lifecycle #install \*\*Annotation:\*\* First-run handshake content. Run once on install, not on every startup. #### R17 — docs.openclaw.ai/reference/templates/HEARTBEAT \*\*Source:\*\* docs.openclaw.ai/reference/templates/HEARTBEAT · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #lifecycle #cron \*\*Annotation:\*\* Periodic check-in instructions fired by cron. The agent’s recurring rhythm. #### R18 — docs.openclaw.ai/reference/AGENTS.default \*\*Source:\*\* docs.openclaw.ai/reference/AGENTS.default · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #openclaw #defaults \*\*Annotation:\*\* OpenClaw’s default agent configuration. Reference baseline for any `AGENTS.md` we write. #### R19 — docs.openclaw.ai/reference/transcript-hygiene \*\*Source:\*\* docs.openclaw.ai/reference/transcript-hygiene · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #transcripts #providers \*\*Annotation:\*\* Provider-specific repair matrix for replaying transcripts across Anthropic, OpenAI Responses, Gemini, and Bedrock Converse. Reason `~/.agents/transcripts/policies/` exists in v5+. #### R20 — docs.openclaw.ai/reference/session-management-compaction \*\*Source:\*\* docs.openclaw.ai/reference/session-management-compaction · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #compaction #ritual \*\*Annotation:\*\* Defines the pre-compaction memory-flush ritual: silent agentic turn before context wipe so the agent saves what matters. The most elegant single mechanism in the OpenClaw spec. #### R21 — docs.openclaw.ai/reference/prompt-caching \*\*Source:\*\* docs.openclaw.ai/reference/prompt-caching · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #caching #performance \*\*Annotation:\*\* Prompt caching reference for cost/latency optimization. Pairs with the api_modes plugin design. #### R22 — docs.openclaw.ai/pi \*\*Source:\*\* docs.openclaw.ai/pi · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #pi \*\*Annotation:\*\* The “Pi” silent agentic turn pattern (NO_REPLY) used in the memory-flush ritual. Convention for invisible-to-user agent self-talk. #### R23 — docs.openclaw.ai/automation/hooks \*\*Source:\*\* docs.openclaw.ai/automation/hooks · \*\*Thread:\*\* T08 · \*\*Tags:\*\* #openclaw #hooks #events \*\*Annotation:\*\* Full 27-event hook catalog. The single most complete agent-lifecycle vocabulary in any published spec. #### R24 — docs.openclaw.ai/automation/standing-orders \*\*Source:\*\* docs.openclaw.ai/automation/standing-orders · \*\*Thread:\*\* T08 · \*\*Tags:\*\* #openclaw #standing-orders #autonomy \*\*Annotation:\*\* Defines standing orders as agent-readable authority declarations distinct from cron triggers. Source of the Authority / Trigger / Approval / Escalation template. #### R25 — docs.openclaw.ai/automation/taskflow \*\*Source:\*\* docs.openclaw.ai/automation/taskflow · \*\*Thread:\*\* T08 · \*\*Tags:\*\* #openclaw #taskflow #orchestration \*\*Annotation:\*\* Multi-step orchestration with revision tracking that survives restart. The “real workflow engine” layer above background tasks. #### R26 — docs.openclaw.ai/tools/multi-agent-sandbox-tools \*\*Source:\*\* docs.openclaw.ai/tools/multi-agent-sandbox-tools · \*\*Thread:\*\* T08 · \*\*Tags:\*\* #openclaw #sandbox #multi-agent \*\*Annotation:\*\* Sandbox tooling for spawning isolated agent instances. Maps to the iii.dev worker-as-primitive model. #### R27 — docs.openclaw.ai/tools/acp-agents \*\*Source:\*\* docs.openclaw.ai/tools/acp-agents · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #acp #protocol \*\*Annotation:\*\* OpenClaw’s implementation of Agent Client Protocol agent endpoints. Reference for how `~/.agents/acp/editors.yaml` should be structured. #### R28 — docs.openclaw.ai/start/wizard \*\*Source:\*\* docs.openclaw.ai/start/wizard · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #openclaw #install #onboarding \*\*Annotation:\*\* Interactive setup wizard reference. Model for what `bin/bootstrap.sh` interactive mode should do. #### R29 — docs.openclaw.ai/gateway \*\*Source:\*\* docs.openclaw.ai/gateway · \*\*Thread:\*\* T08 · \*\*Tags:\*\* #openclaw #gateway #messaging \*\*Annotation:\*\* The 20-platform messaging adapter layer (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, etc.). Drives `~/.agents/gateway/` in v4+. #### R30 — docs.openclaw.ai/gateway/configuration \*\*Source:\*\* docs.openclaw.ai/gateway/configuration · \*\*Thread:\*\* T08 · \*\*Tags:\*\* #openclaw #gateway #config \*\*Annotation:\*\* Per-platform gateway configuration spec. Reference for `gateway/platforms/<name>.toml` schemas. #### R31 — docs.openclaw.ai/gateway/health \*\*Source:\*\* docs.openclaw.ai/gateway/health · \*\*Thread:\*\* T08 · \*\*Tags:\*\* #openclaw #gateway #observability \*\*Annotation:\*\* Health check endpoints and observability for gateway processes. Pairs with `state/processes/` design. ### Protocols & Specs #### R32 — agents.md \*\*Source:\*\* agents.md · \*\*Thread:\*\* T02 (implicit) · \*\*Tags:\*\* #spec #protocol #standard \*\*Annotation:\*\* The agents.md standard for project-level operating instructions. Codex made AGENTS.md the de facto filename; Gemini supports aliasing. #### R33 — agentskills.io \*\*Source:\*\* agentskills.io · \*\*Thread:\*\* T05 (implicit) · \*\*Tags:\*\* #spec #skills #progressive-disclosure \*\*Annotation:\*\* Skill format specification: SKILL.md entry point, references/ on demand, scripts/ on call. Conformance target for every skill in `~/.agents/skills/`. #### R34 — agentclientprotocol.com \*\*Source:\*\* agentclientprotocol.com · \*\*Thread:\*\* T07 · \*\*Tags:\*\* #spec #acp #editor-protocol \*\*Annotation:\*\* ACP is to agents what LSP is to languages — standardized JSON-RPC over stdio between editor (Zed / JetBrains / VS Code) and agent. Orthogonal to MCP, which is agent ↔ tool. #### R35 — soul.md \*\*Source:\*\* soul.md · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #spec #soul #identity \*\*Annotation:\*\* Steipete’s SOUL.md tradition — separating identity context (who) from project context (how). Crystallizes the two-layer split that became v5’s workspace/config separation. ### Memory & Runtime #### R36 — agent-memory.dev \*\*Source:\*\* agent-memory.dev · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #memory #runtime \*\*Annotation:\*\* Triple-stream memory runtime (BM25 + vector + knowledge graph) installed via `npm i -g @agentmemory/agentmemory`. One reference implementation for the `plugins/memory/` slot. #### R37 — github.com/mem0ai/mem0 \*\*Source:\*\* github.com/mem0ai/mem0 · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #memory #runtime \*\*Annotation:\*\* Alternative memory provider. Slots beside agent-memory under `plugins/memory/`. #### R38 — thedotmack/claude-mem \*\*Source:\*\* github.com/thedotmack/claude-mem · \*\*Thread:\*\* T09 · \*\*Tags:\*\* #memory #runtime #reference-implementation \*\*Annotation:\*\* Apache-2.0 persistent memory plugin: 5 lifecycle hooks (SessionStart → UserPromptSubmit → PostToolUse → Summary → SessionEnd), SQLite + ChromaDB, web viewer on :37777. Designated the \*\*reference default\*\* for `plugins/memory/`. Works across Claude Code, OpenClaw, Codex, Gemini, Hermes, Copilot, OpenCode. ### Frameworks & Tooling #### R39 — iii.dev \*\*Source:\*\* iii.dev · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #framework #primitive #orchestration \*\*Annotation:\*\* Worker / function / trigger as a single addressable primitive across languages. Slots into the modular-synth conductor framing — each worker is an oscillator, each trigger a patch cable. #### R40 — github.com/snyk/agent-scan \*\*Source:\*\* github.com/snyk/agent-scan · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #trust #security #audit \*\*Annotation:\*\* Snyk’s agent security scanner. Outputs go to `trust/audit/` for rotated review. #### R41 — ai.gendigital.com/agent-trust-hub \*\*Source:\*\* ai.gendigital.com/agent-trust-hub · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #trust #governance \*\*Annotation:\*\* Gen Digital’s agent trust governance hub. Reference for organizational trust patterns beyond individual-machine `trust/` configs. #### R42 — github.com/openprose \*\*Source:\*\* github.com/openprose · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #framework #prose \*\*Annotation:\*\* Open-source prose-generation framework. Referenced as adjacent design space without direct integration. #### R43 — gist Richard-Weiss/efe157692991535403bd7e7fb20b6695 \*\*Source:\*\* gist.github.com/Richard-Weiss/efe157692991535403bd7e7fb20b6695 · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #soul #example \*\*Annotation:\*\* Worked example of an agent SOUL.md in the wild. Stylistic reference for writing the canonical `workspace/SOUL.md`. ### Discovery & Inventory #### R44 — e2b-dev/awesome-ai-agents \*\*Source:\*\* github.com/e2b-dev/awesome-ai-agents · \*\*Thread:\*\* T09 · \*\*Tags:\*\* #catalog #discovery \*\*Annotation:\*\* Curated directory of entire agents (not skills or subagents — full agents). Source for `a2a/peers.yaml` candidates and for surveying the agentic-framework landscape. #### R45 — alebcay/awesome-shell \*\*Source:\*\* github.com/alebcay/awesome-shell · \*\*Thread:\*\* T09 · \*\*Tags:\*\* #catalog #shell #tool-augmentation \*\*Annotation:\*\* Curated shell-tooling catalog. Augments `workspace/TOOLS.md` with reference-only links rather than installable bundles. Archetype 5 (tool-catalogs) in the v7 manifest. #### R46 — DeadWaveWave/opencove \*\*Source:\*\* github.com/DeadWaveWave/opencove · \*\*Thread:\*\* T04 · \*\*Tags:\*\* #fork #openclaw \*\*Annotation:\*\* OpenClaw-adjacent fork or community implementation. Referenced as evidence of the OpenClaw template family’s spread. ### Routing #### R47 — manifest.build \*\*Source:\*\* manifest.build · \*\*Thread:\*\* T10 · \*\*Tags:\*\* #routing #llm-router #reference-implementation \*\*Annotation:\*\* Open-source LLM router with smart routing by complexity tier, fallback chains, budgets, and multi-provider (API key + subscription + local Ollama). Drop-in OpenAI-compatible. Designated reference implementation for the new `routing/` slot in v7. Causes a naming collision with our `manifest.yaml`; recommended renaming to `agents-lock.yaml`. ----- ## §3 · Uploaded Documents (D##) ### D01 — hermes-agent/ folder hierarchy \*\*Source:\*\* Uploaded in T06 · \*\*Tags:\*\* #hermes #runtime #reference-implementation \*\*Annotation:\*\* NousResearch’s Hermes agent project tree showing a production-grade implementation of every concept under design: `AIAgent` core loop, `prompt_builder`, `context_engine` ABC, `memory_provider` ABC, three API modes, 20 gateway platforms, ACP adapter, cron scheduler, batch runner, toolsets, plugin system, SQLite+FTS5 session storage. Reframed the entire design from “configuration spec” to “config consumed by a runtime like this one.” ----- ## §4 · Generated Artifacts (A##) The artifacts I produced across the conversation, in chronological order. ### A01 — Generalized agent-workspace tree \*\*Thread:\*\* T01 · \*\*Tags:\*\* #workspace-spec #v0 \*\*Annotation:\*\* Opening synthesis of standard folders (`.agent/`, `skills/`, `memory/`, `tools/`, `prompts/`, `orchestration/`, `inputs/`, `outputs/`, `data/`, `logs/`, `evals/`, `hooks/`, `docs/`) with design principles around the layer split. Foundation that every later iteration extended rather than replaced. ### A02 — Per-tool install manifestations \*\*Thread:\*\* T02 · \*\*Tags:\*\* #claude-code #codex #gemini #opencode #reference \*\*Annotation:\*\* Documented filesystem layouts for `~/.claude/`, `~/.codex/`, `~/.gemini/`, `~/.config/opencode/` after install, including config files, agent dirs, command dirs, skill dirs, plugin dirs, session stores. The reference card that motivated the unified design. ### A03 — `~/.agents/` v1 dotfile sketch \*\*Thread:\*\* T03 · \*\*Tags:\*\* #dotfile-design #v1 #symlinks \*\*Annotation:\*\* First unified design with `shared/` (symlinked into each tool) and `configs/` (tool-specific). Included POSIX `bootstrap.sh` and PowerShell `bootstrap.ps1` installers. Noted the four config files that resist unification. ### A04 — `~/.agents/` v2 with OpenClaw absorption \*\*Thread:\*\* T04 · \*\*Tags:\*\* #dotfile-design #v2 #openclaw #soul \*\*Annotation:\*\* Added the `workspace/` layer (SOUL/IDENTITY/USER/TOOLS/BOOT/BOOTSTRAP/HEARTBEAT/MEMORY), the `memory/` runtime with agent-memory integration, `shared/workers/` for iii primitives, the `trust/` layer, and named the seven drift cadences from soul (years) to per-request observations. ### A05 — `~/.agents/` v3 canonical layout \*\*Thread:\*\* T05 · \*\*Tags:\*\* #dotfile-design #v3 #manifest #provenance \*\*Annotation:\*\* Pivoted on the Codex-native `~/.agents/skills/` discovery. Introduced `manifest.yaml`, `_sync.lock`, `_registry.md` for provenance. Adopted the muratcankoylan three-theme skill taxonomy. Drafted the eight-tool symlink topology to a single canonical skill store. ### A06 — Bootstrap and sync scripts (POSIX + PowerShell) \*\*Thread:\*\* T03, T05 · \*\*Tags:\*\* #installer #scripts #provenance \*\*Annotation:\*\* Drafted `bin/bootstrap.sh`, `bin/bootstrap.ps1`, `bin/sync-skills.sh`. Lays symlinks into Claude/Codex/Gemini/OpenCode/Cursor/Windsurf/Antigravity/Copilot and clones the named source bundles. Never finalized for actual execution; remains a v3 draft pending v6 corrections. ### A07 — `~/.agents/` v4 with profiles, plugins, toolsets \*\*Thread:\*\* T06 · \*\*Tags:\*\* #dotfile-design #v4 #hermes #plugins \*\*Annotation:\*\* Folded in five concepts from Hermes: profiles (multiple identities sharing capability), pluggable subsystems with ABCs (context_engine, memory, api_modes), toolsets distinct from skills, the gateway adapter layer, the scheduler / acp / trajectories / state subdivisions. First version with the identity/capability/runtime trichotomy explicit. ### A08 — `~/.agents/` v5 with workspace/config split \*\*Thread:\*\* T07 · \*\*Tags:\*\* #dotfile-design #v5 #workspace #rituals \*\*Annotation:\*\* Corrected v4’s biggest error: split `~/.agents/` (config root, machine-local, never committed) from `~/.agents-workspace/` (git-backed private soul). Introduced `rituals/` for named lifecycle choreographies (boot, bootstrap, heartbeat, memory-flush, daily-reset, dreaming), `transcripts/policies/` for provider-specific hygiene, `mcp/` + `acp/` + `a2a/` as three orthogonal protocol slots, and `memory-wiki/` for provenance-rich knowledge. ### A09 — `~/.agents/` v6 with automation/ \*\*Thread:\*\* T08 · \*\*Tags:\*\* #dotfile-design #v6 #automation #hooks \*\*Annotation:\*\* Split autonomy into five distinct mechanisms (Standing Orders / Cron / Hooks / Background Tasks / TaskFlow) in `automation/`. Catalogued the 27-event hook vocabulary as `automation/hooks/_events.md`. Added `_precedence.md` for the bundled<plugin<managed<workspace gradient. Added `trust/approval-policies.yaml` for `requireApproval` hook defaults. Identified the four mandatory sections any canonical `AGENTS.md` must include. ### A10 — `manifest.yaml` v2 with five archetypes \*\*Thread:\*\* T09 · \*\*Tags:\*\* #manifest #provenance #catalogs \*\*Annotation:\*\* Reworked the manifest from listing bundles to listing five supply-chain archetypes (catalogs / bundles / corpora / specs / tool-catalogs), each with distinct install semantics. Pinned 20+ named sources across the entire conversation. Reframed the dotfile as a package manager wearing a filesystem layout. ### A11 — `workspace/agents/` taxonomy mapping \*\*Thread:\*\* T09 · \*\*Tags:\*\* #subagents #taxonomy #voltagent \*\*Annotation:\*\* Adopted VoltAgent’s 10-category subagent taxonomy. Distinguished skill-taxonomy (fundamentals/architecture/operations — what you’re learning) from agent-taxonomy (10 dev-org roles — who you delegate to). Required `role_class` frontmatter field for least-privilege permission gradient. ### A12 — `routing/` slot for v7 \*\*Thread:\*\* T10 · \*\*Tags:\*\* #routing #v7-addendum \*\*Annotation:\*\* Added `~/.agents/routing/` with `providers.yaml`, `routes.yaml`, `fallbacks.yaml`, `budgets.yaml` to handle provider routing distinct from wire-protocol api_modes. Recommended renaming `manifest.yaml` → `agents-lock.yaml` to avoid the manifest.build collision. ### A13 — This manifest \*\*Thread:\*\* T11 · \*\*Tags:\*\* #meta #manifest #archival \*\*Annotation:\*\* The annotated bibliography you are reading. Catalogs all 11 threads, 47 external resources, 1 uploaded document, and 13 generated artifacts. ----- ## §5 · Tag Index For cross-reference. Each tag lists the entries it appears in. |Tag |Entries | |-------------------------|---------------------------------| |#acp |R27, R34, A08 | |#agent-catalog |R03, R44 | |#agents-md |R11, R32 | |#archival |T11, A13 | |#automation |T08, A09 | |#boot |R15 | |#caching |R21 | |#catalog |R01, R02, R03, R44, R45 | |#claude-code |T02, R03, A02 | |#codex |T02, T05, A02 | |#compaction |T07, R20 | |#context-engineering |R04, T05 | |#cron |T08, R17 | |#defaults |R18 | |#discovery |R44 | |#dotfile-design |T03, A03, A04, A05, A07, A08, A09| |#epistemic |R06 | |#events |R23 | |#example |R43 | |#framework |R39, R42 | |#foundation |T01 | |#gateway |R29, R30, R31 | |#gemini |T02, A02 | |#governance |R41 | |#hermes |T06, D01, A07 | |#hooks |T08, R23, A09 | |#identity |T04, R10, R12, R35 | |#install |R16, R28 | |#installer |A06 | |#lifecycle |R15, R16, R17 | |#llm-router |R47 | |#manifest |T05, A10, A13 | |#manifest-v2 |T09 | |#memory |T04, T07, R09, R36, R37, R38 | |#memory-tiers |T07, R09 | |#messaging |R29 | |#meta |T11, A13 | |#multi-agent |R26 | |#multi-tool |R02 | |#naming-collision |T10 | |#observability |R31 | |#onboarding |R28 | |#openclaw |T04, T07, T08, R08–R31, R46 | |#opencode |T02, A02 | |#orchestration |R25, R39 | |#performance |R21 | |#pi |R22 | |#plugins |T06, A07 | |#prompt-engineering |R05, R07 | |#prose |R42 | |#protocol |T07, R27, R32, R33, R34 | |#provenance |T04, T05, T09, A05, A06, A10 | |#reference |A02 | |#reference-implementation|R38, R47, D01 | |#registry |R01 | |#ritual |T07, R20, A08 | |#routing |T10, R47, A12 | |#runtime |T06, R36, R37, R38, D01 | |#safety |R06 | |#sandbox |R26 | |#scripts |A06 | |#security |R40 | |#shell |R45 | |#skills |T05, R01, R02, R04, R05, R06, R33| |#soul |T04, R10, R35, R43, A04 | |#spec |R32, R33, R34, R35 | |#standard |R32 | |#standing-orders |T08, R24 | |#subagents |T09, R03, A11 | |#symlinks |T03, A03 | |#taskflow |T08, R25 | |#taxonomy |R03, A11 | |#tiers |R09 | |#tool-augmentation |R45 | |#tools |R14 | |#toolsets |T06, A07 | |#transcripts |R19 | |#trust |R40, R41 | |#user-profile |R13 | |#v0 |T01, A01 | |#v1 |T03, A03 | |#v2 |T04, A04 | |#v3 |T05, A05 | |#v4 |T06, A07 | |#v5 |T07, A08 | |#v6 |T08, A09 | |#v7 |T09 | |#v7-addendum |T10, A12 | |#voltagent |A11 | |#vibe |R12 | |#workspace |T07, R08, A08 | |#workspace-spec |T01, A01 | ----- ## §6 · Counts - \*\*Threads:\*\* 11 (T01–T11) - \*\*External Resources:\*\* 47 (R01–R47) - \*\*Uploaded Documents:\*\* 1 (D01) - \*\*Generated Artifacts:\*\* 13 (A01–A13) - \*\*Total entries:\*\* 72 ## §7 · Unbuilt Deliverables (Roadmap) Three concrete deliverables proposed across multiple threads, still uncommitted: 1. \*\*Canonical `workspace/AGENTS.md`\*\* — eight-organ standing orders for {OS.me}, Execute-Verify-Report rule, memory write policy. 1. \*\*Canonical `workspace/SOUL.md`\*\* — the file an inheriting agent would read ten years from now to recover the conductor identity. 1. \*\*`bin/bootstrap.sh` v6\*\* — actual installable script laying both roots, initializing the workspace git repo, laying eight symlinks, seeding all eight workspace template files.Show moreShow less

## A: 
I’ll treat this as the project manifest handoff and convert it into an actionable build translation: canonical root model, repo/file targets, unresolved contradictions, and the next three concrete artifacts.

Received. I do **not** find an existing accessible GitHub repo named `agents-dotfile-spec`, so I’m treating this as the canonical project manifest / handoff rather than as an existing repository state.

# Translation

`PROJ:agents-dotfile-spec` is not merely a dotfile layout. It is a **personal agent operating substrate**.

Its actual thesis is:

```plain text
Create one canonical agent home that separates identity, memory, skills, tools, automation, routing, protocols, trust, and runtime adapters, then refracts that home outward into Claude Code, Codex, Gemini CLI, OpenCode, Cursor, Windsurf, Antigravity, and Copilot.
```

The deepest structure is:

```plain text
identity      = SOUL.md / IDENTITY.md / USER.mdlaw           = AGENTS.md / standing orders / trust policiescapability    = skills / subagents / toolsetsmemory        = working / curated / commitments / wiki / transcriptsautomation    = hooks / cron / taskflow / background tasksprotocols     = MCP / ACP / A2A / gatewayrouting       = providers / routes / fallbacks / budgetsrefraction    = per-tool projected pathsruntime       = tool-specific configs and local state
```

# Canonical architecture decision

The manifest has one major resolved design principle:

```plain text
workspace ≠ config root
```

So the final system should use **two roots**.

```plain text
AGENTS_CONFIG_ROOT="${AGENTS_CONFIG_ROOT:-${HOME}/.agents}"AGENTS_WORKSPACE_ROOT="${AGENTS_WORKSPACE_ROOT:-${HOME}/.agents-workspace}"
```

## Root 1: machine-local config

```plain text
${AGENTS_CONFIG_ROOT}/  bin/  config/  adapters/  routing/  mcp/  acp/  a2a/  gateway/  memory/  transcripts/  trust/  state/  cache/  logs/
```

This root should **not** be treated as the sacred identity layer. It is mutable machine infrastructure.

## Root 2: git-backed private workspace

```plain text
${AGENTS_WORKSPACE_ROOT}/  AGENTS.md  SOUL.md  IDENTITY.md  USER.md  TOOLS.md  BOOT.md  BOOTSTRAP.md  HEARTBEAT.md  MEMORY.md  skills/  agents/  toolsets/  rituals/  standing-orders/  automation/  memory-wiki/  docs/  manifests/
```

This root is the “soul/workspace” layer. It should be private, versioned, and recoverable.

# The necessary correction

Your manifest still contains a tension:

```plain text
v1-v5: symlink topologylater logic: generated/refraction topologyyour preference: avoid fragile symlinks
```

Given your newer refractive model, the stronger pattern is:

```plain text
author onceproject outwardverify parityavoid symlink dependency
```

So instead of making every tool point into one shared folder with symlinks, use a **refraction engine**:

```plain text
${AGENTS_WORKSPACE_ROOT}/skills/  = canonical source${HOME}/.claude/skills/${HOME}/.agents/skills/${HOME}/.gemini/skills/${HOME}/.config/opencode/skills/${HOME}/.cursor/skills/${HOME}/.codeium/windsurf/skills/${HOME}/.copilot/skills/  = generated apertures
```

Each generated aperture should contain a small marker:

```plain text
REFRACTED_FROM.txtSOURCE_SHA256GENERATED_AT_UTCTARGET_TOOL
```

# The merged v7 spine

The final version is not v6 plus an addendum. It should be renamed:

```plain text
v7 = workspace/config split + automation layer + routing layer + refraction layer
```

## Final top-level map

```plain text
${AGENTS_WORKSPACE_ROOT}/  AGENTS.md  SOUL.md  IDENTITY.md  USER.md  TOOLS.md  BOOT.md  BOOTSTRAP.md  HEARTBEAT.md  MEMORY.md  skills/    _registry.md    agents-lock.yaml    fundamentals/    architecture/    operations/    epistemic/    prompt-engineering/    context-engineering/  agents/    core-development/    language-specialists/    infrastructure/    quality-security/    data-ai/    dev-experience/    specialized-domains/    business-product/    meta-orchestration/    research-analysis/  toolsets/  rituals/  standing-orders/  automation/    hooks/    cron/    background-tasks/    taskflow/    _precedence.md  memory-wiki/  manifests/    agents-lock.yaml    sources.yaml    refractions.yaml    inventory.yaml  docs/
```
```plain text
${AGENTS_CONFIG_ROOT}/  bin/    bootstrap.sh    refract-skills.sh    verify-refractions.sh    sync-sources.sh  adapters/    claude/    codex/    gemini/    opencode/    cursor/    windsurf/    antigravity/    copilot/  routing/    providers.yaml    routes.yaml    fallbacks.yaml    budgets.yaml  mcp/  acp/  a2a/  gateway/  memory/  transcripts/  trust/  state/  cache/  logs/
```

# Immediate deliverables

Your manifest says three deliverables remain unbuilt. I would treat them as **build order**, not merely roadmap.

## 1. `workspace/AGENTS.md`

Purpose:

```plain text
Defines law, procedure, permissions, memory policy, execution discipline, and cross-agent conduct.
```

Mandatory sections:

```plain text
1. Operating Doctrine2. Execute-Verify-Report Rule3. Memory Write Policy4. Tool / Trust / Approval Policy5. Workspace Boundaries6. Refraction Rules7. Handoff Rules8. Failure / Escalation Rules
```

## 2. `workspace/SOUL.md`

Purpose:

```plain text
Defines conductor identity, long-horizon continuity, values, stylistic constraints, and recovery semantics.
```

This is not a prompt file. It is the inheritance file.

It should answer:

```plain text
Who is the conductor?What is the system trying to preserve?What must never be flattened?What is allowed to evolve?What is the agent’s relation to the human?What does continuity mean after tool death, model drift, or repo loss?
```

## 3. `bin/bootstrap.sh`

Purpose:

```plain text
Creates the two roots, seeds canonical workspace files, installs adapters, projects refractions, and validates parity.
```

It should perform:

```plain text
mkdir -p "${AGENTS_CONFIG_ROOT}"mkdir -p "${AGENTS_WORKSPACE_ROOT}"seed workspace templatesseed config templatesinitialize git repo in workspaceinstall/refraction targets for supported toolswrite agents-lock.yamlrun verify-refractions.shrun health report
```

# The project’s real missing fourth deliverable

The manifest lists three unbuilt deliverables, but the architecture now requires a fourth:

```plain text
bin/refract-skills.sh
```

Without this, the system falls back into brittle symlink thinking.

This script should copy from:

```plain text
${AGENTS_WORKSPACE_ROOT}/skills/
```

into:

```plain text
${HOME}/.agents/skills/${HOME}/.claude/skills/${HOME}/.gemini/skills/${HOME}/.config/opencode/skills/
```

Then generate:

```plain text
${AGENTS_WORKSPACE_ROOT}/manifests/refractions.yaml${AGENTS_WORKSPACE_ROOT}/manifests/REFRACTION.sha256
```

# Final compression

The manifest can now be collapsed into this operating formula:

```plain text
PROJ:agents-dotfile-spec=private agent workspace+ local runtime config+ canonical skill/subagent corpus+ memory substrate+ automation substrate+ protocol substrate+ routing substrate+ generated tool-specific apertures+ checksum-verifiable refraction
```

The next move is to stop iterating the abstract tree and generate the repo skeleton:

```plain text
AGENTS.mdSOUL.mdbin/bootstrap.shbin/refract-skills.shbin/verify-refractions.shmanifests/agents-lock.yamlmanifests/refractions.yaml
```

