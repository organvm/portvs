# Specification: ORGANVM Unified Superproject

## 1. Meta
- **ID:** ORG-SPEC-001
- **Title:** The ORGANVM Unified Superproject
- **Status:** DRAFT
- **Author:** Gemini CLI (Agent)
- **Date:** 2026-05-19

## 2. Context & Problem Statement
ORGANVM currently exists as 8 distinct GitHub organizations. While this provides excellent semantic isolation mirroring the `UMFAS` framework, it introduces severe operational friction:
- Context switching between 8 different GitHub namespaces.
- Fragmented CI/CD pipelines and secrets management.
- Complex developer onboarding.

**The False Dilemma:** We must choose between Semantic Purity (8 Orgs) and Operational Efficiency (1 Mega-Org).

## 3. The Solution: Headless Orgs & The Agentic Superproject
We adopt **Strategy 1: Unified Superproject**, but elevate it from a simple git repository to an **Agentic Operating Environment**. 

The 8 GitHub organizations will be treated as "headless storage." Humans and AI agents will interact *exclusively* with the `organvm-unified--superproject`.

### 3.1 Architectural Principles
1. **The Superproject is the OS:** The root repository is the sole entry point. Sub-orgs are treated as mounted drives.
2. **Submodule Abstraction:** Git submodules are used under the hood, but their complexity is abstracted away from human developers via tooling.
3. **Centralized Governance:** All overarching policies, `.github/workflows`, and fleet orchestrations (`fleet.yaml`) live in the Superproject and are pushed down to sub-orgs.

## 4. System Architecture

### 4.1 Directory Structure
```text
organvm-unified--superproject/
├── .github/                  # Centralized CI/CD templates and workflows
├── .organvm/                 # CLI configuration and agent state
│   ├── fleet.yaml            # Cross-agent orchestration state
│   └── fossil-record.jsonl   # Unified session archival
├── docs/                     # Aggregated documentation (auto-generated)
│   └── architecture/         # Auto-regenerated timeline and indices
├── tools/                    # Superproject CLI and automation scripts
│
# Mounted "Headless" Sub-Organizations (Git Submodules)
├── meta-organvm/             # Admin & Governance Hub
├── organvm-i-theoria/        # Knowledge Layer
├── organvm-ii-poiesis/       # Creation Layer
├── organvm-iii-ergon/        # Production Layer
├── organvm-iv-taxis/         # Orchestration Layer
├── organvm-v-logos/          
├── organvm-vi-koinonia/      
└── organvm-vii-kerygma/      
```

### 4.2 Component Workflows

#### 4.2.1 The Sync Engine (CI/CD)
A GitHub Action running in the Superproject will act as the "Sync Engine".
- **Trigger:** Nightly, or on pushes to `.github/` or `.editorconfig` in the Superproject.
- **Action:** Propagates standard workflows, repository rules, and configuration files down to all repositories across the 8 sub-organizations.

#### 4.2.2 The Architecture Generator
The current static python scripts (`arch_evolution.py`) will be integrated into the Superproject.
- **Trigger:** Weekly cron job via GitHub Actions.
- **Action:** Queries the GitHub API, parses commits across all 8 orgs, and regenerates the 3-document suite (`SUMMARY`, `TIMELINE`, `EVOLUTION`) into the Superproject's `docs/architecture/` folder.

#### 4.2.3 Submodule Friction Mitigation
To prevent detached HEAD states and push failures:
- Developers will use a provided `organvm-cli` (or a standardized `make` file).
- Example: `make sync` will automatically run `git submodule update --init --recursive --remote`.
- Example: `make push-all` will iterate through submodules, checking for unpushed commits on tracked branches before pushing the Superproject pointer.

## 5. Security & Permissions
- **Principle of Least Privilege:** Teams are granted write access only to the specific sub-org repositories they need.
- **Superproject Access:** All developers have read access to the Superproject. Only Core Architects have write access to merge Superproject pointer updates.
- **Secrets:** Enterprise-wide secrets are managed at the Superproject level and injected into sub-org repositories via the Sync Engine.

## 6. Implementation Phases

**Phase 1: Initialization**
- Create `organvm-unified--superproject` in `meta-organvm`.
- Mount the 8 superprojects of the sub-organizations as submodules.
- Establish the `make` file for basic sync operations.

**Phase 2: Automation Integration**
- Move the architecture timeline scripts into the Superproject.
- Setup GitHub Actions to auto-regenerate the documentation.

**Phase 3: Centralized Governance**
- Move `.editorconfig` and core `.github/workflows` to the Superproject.
- Implement the Sync Engine to push these standards down to the sub-orgs.

## 7. Success Criteria
- [ ] A new developer can clone `organvm-unified--superproject` and run `make init` to get the entire ecosystem locally without navigating 8 GitHub org pages.
- [ ] The architecture timeline updates itself automatically without human intervention.
- [ ] A change to a global CI pipeline only needs to be authored once in the Superproject.
