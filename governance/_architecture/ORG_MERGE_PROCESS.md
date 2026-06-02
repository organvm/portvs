# GitHub Enterprise: Organization Merge Process via CLI

## ⚠️ CRITICAL: GitHub Enterprise Limitation

**As of 2026-05-19:** GitHub does NOT provide a native API or CLI command for merging organizations.

Organizations are **atomic units** that cannot be merged programmatically. You must:
1. **Manually migrate repositories** (one by one)
2. **Reassign team memberships** (manual or via script)
3. **Update branch protections** (per repo)
4. **Redirect org webhooks** (if applicable)
5. **Delete the empty org** (after migration)

---

## 🎯 Organization Merge Strategy (For ORGANVM)

Given your 8-org structure, here's the recommended approach:

### Option A: Consolidate via Superproject (RECOMMENDED)
Keep organizations separate but use submodule orchestration.

```bash
# Create unified reference in one superproject
organvm-unified--superproject/
├── submodule: meta-organvm (as reference)
├── submodule: organvm-i-theoria--superproject
├── submodule: organvm-ii-poiesis--superproject
├── submodule: organvm-iii-ergon--superproject
├── submodule: organvm-iv-taxis--superproject
├── submodule: organvm-v-logos--superproject
├── submodule: organvm-vi-koinonia--superproject
└── submodule: organvm-vii-kerygma--superproject

# Benefits:
✓ Preserves org structure (no GitHub limits)
✓ Maintains separate permissions/billing
✓ Single entry point for navigation
✓ No data migration required
✗ Still requires manual navigation
```

### Option B: Gradual Consolidation (SAFE)
Merge non-critical orgs into primary org over time.

```bash
# Phase 1: Migrate organvm-v-logos → organvm-iv-taxis
# Phase 2: Migrate organvm-vi-koinonia → organvm-iv-taxis
# Phase 3: Migrate organvm-vii-kerygma → organvm-iv-taxis
# Result: 5 orgs → 2 orgs (meta + core)

# Benefits:
✓ Testable in phases
✓ Lower risk per phase
✓ Can roll back each phase
✗ Time-consuming (multiple migrations)
```

### Option C: Full Consolidation (RISKY)
Merge everything into one organization.

```bash
# Result: Single mega-org with 35+ repos
# Challenges:
✗ GitHub org limits (500K+ repos, 5K+ teams)
✗ Permission complexity (many teams in 1 org)
✗ Billing consolidation needed
✗ Hard to undo
✓ Single permission model
```

---

## 🔧 Detailed: Repository Migration (Building Block)

### Prerequisites
```bash
# GitHub Enterprise access (org owner)
gh auth login --scopes admin:org,repo
gh auth status

# Verify CLI version (need 2.0+)
gh --version

# Verify your membership
gh org list --no-limit
```

### Step 1: Prepare Source Repository

```bash
# Clone the repo to migrate
git clone https://github.com/SOURCE_ORG/REPO.git
cd REPO

# Create bare clone (for migration)
cd ..
git clone --bare REPO REPO.git
cd REPO.git

# Mirror fetch (all refs, all history)
git fetch --mirror
```

### Step 2: Create Destination Repository

```bash
# Create new repo in target org
gh repo create TARGET_ORG/REPO \
  --private \
  --source=none \
  --remote=origin \
  --push

# Or via web if automation not available
# https://github.com/organizations/TARGET_ORG/repositories/new
```

### Step 3: Push All History

```bash
# Push with complete history and all refs
git push --mirror https://github.com/TARGET_ORG/REPO.git

# Or if using SSH
git push --mirror git@github.com:TARGET_ORG/REPO.git
```

### Step 4: Update Local Repos & CI/CD

```bash
# Update all local clones
for clone in ~/path/to/clones/*; do
  cd "$clone"
  git remote set-url origin https://github.com/TARGET_ORG/REPO.git
  git remote -v
done

# Update CI/CD pipelines
# GitHub Actions: Update .github/workflows/
# Update any webhook URLs
# Update branch protection rules
# Update issue/PR templates
```

### Step 5: Reassign Teams & Permissions

```bash
# Get all teams in source org
gh api orgs/SOURCE_ORG/teams --paginate -q '.[] | .slug'

# For each team, add to repo in target org
gh api repos/TARGET_ORG/REPO/teams \
  -f team_slug='TEAM_NAME' \
  -f permission='push'

# Verify permissions
gh repo view TARGET_ORG/REPO --json repositoryTopics,teams
```

### Step 6: Transfer Ownership (if applicable)

```bash
# If repo admin, can transfer directly
gh repo edit SOURCE_ORG/REPO --owner TARGET_ORG

# Note: This changes the URL!
# Old: https://github.com/SOURCE_ORG/REPO
# New: https://github.com/TARGET_ORG/REPO
```

### Step 7: Archive & Delete Source

```bash
# Archive original (prevents accidents)
gh repo archive SOURCE_ORG/REPO --confirm

# Or delete if migration verified
gh repo delete SOURCE_ORG/REPO --confirm
```

---

## 📋 CLI Commands Reference

### List Organizations
```bash
gh org list --no-limit
gh api graphql -f query='
  query {
    enterprise(slug: "meta-organvm") {
      organizations(first: 100) {
        nodes { login }
      }
    }
  }
'
```

### List Repositories in Org
```bash
gh repo list ORG_NAME --no-limit --json name,owner

# Or specific format
gh api orgs/ORG_NAME/repos --paginate -q '.[] | {name, owner: .owner.login}'
```

### Get Repository Details
```bash
gh repo view ORG/REPO --json \
  description,owner,isPrivate,createdAt,url

# Full JSON export
gh api repos/ORG/REPO | jq .
```

### Create Batch Migration Script

```bash
#!/bin/bash
set -euo pipefail

SOURCE_ORG="$1"
TARGET_ORG="$2"

# Get all repos in source org
REPOS=$(gh api orgs/$SOURCE_ORG/repos --paginate -q '.[] | .name')

for REPO in $REPOS; do
  echo "Migrating $SOURCE_ORG/$REPO → $TARGET_ORG/$REPO"
  
  # Clone bare
  git clone --bare https://github.com/$SOURCE_ORG/$REPO.git
  
  # Create target repo
  gh repo create $TARGET_ORG/$REPO --private --source=none
  
  # Mirror push
  cd $REPO.git
  git push --mirror https://github.com/$TARGET_ORG/$REPO.git
  cd ..
  
  # Cleanup
  rm -rf $REPO.git
  
  echo "✓ Complete: $TARGET_ORG/$REPO"
done
```

---

## 🎯 For ORGANVM: Recommended Approach

### If Keeping 8 Orgs (Recommended)

Create unified orchestrator:

```bash
# Create new superproject
gh repo create meta-organvm/organvm-unified--superproject \
  --private \
  --description "Unified ORGANVM enterprise reference" \
  --source=none

# Add all orgs as submodules
cd organvm-unified--superproject

git submodule add https://github.com/meta-organvm/meta-organvm--superproject
git submodule add https://github.com/organvm-i-theoria/organvm-i-theoria--superproject
git submodule add https://github.com/organvm-ii-poiesis/organvm-ii-poiesis--superproject
git submodule add https://github.com/organvm-iii-ergon/organvm-iii-ergon--superproject
git submodule add https://github.com/organvm-iv-taxis/organvm-iv-taxis--superproject
git submodule add https://github.com/organvm-v-logos/organvm-v-logos--superproject
git submodule add https://github.com/organvm-vi-koinonia/organvm-vi-koinonia--superproject
git submodule add https://github.com/organvm-vii-kerygma/organvm-vii-kerygma--superproject

git commit -m "feat: add all org superprojects as unified reference"
git push origin main
```

### If Consolidating (Advanced)

```bash
# Migrate non-critical orgs into meta-organvm

# Step 1: Migrate organvm-v-logos repos
for repo in $(gh api orgs/organvm-v-logos/repos --paginate -q '.[] | .name'); do
  # Use repo migration script above
done

# Step 2: Migrate organvm-vi-koinonia repos
# Step 3: Migrate organvm-vii-kerygma repos

# Step 4: Delete empty organizations
gh api -X DELETE orgs/organvm-v-logos
gh api -X DELETE orgs/organvm-vi-koinonia
gh api -X DELETE orgs/organvm-vii-kerygma
```

---

## ⚠️ Gotchas & Considerations

### 1. URL Changes
- Repositories moved to new org have new URLs
- All local clones must be updated
- CI/CD pipelines must be reconfigured
- Webhook URLs must be updated

### 2. Permissions
- Team memberships don't auto-transfer
- Access controls must be manually reassigned
- Org owners may have different permissions

### 3. Branch Protection Rules
- Not transferred with repos
- Must be reapplied in target org

### 4. GitHub Actions Secrets
- Not transferred with repos
- Must be recreated in target org

### 5. Issue & PR Redirects
- Old URLs won't auto-redirect
- No native GitHub redirect service

### 6. Webhook Configuration
- Webhooks tied to old org
- Must be reconfigured for new location

### 7. GitHub Pages
- If org has GitHub Pages site
- May break after migration
- Update DNS/CNAME if applicable

---

## 🔍 Verification Checklist

After migration, verify:

```bash
# [ ] All repos transferred
gh api orgs/TARGET_ORG/repos --paginate -q '.[] | .name' | wc -l

# [ ] All refs preserved
git ls-remote TARGET_ORG/REPO | wc -l

# [ ] Teams reassigned
gh api repos/TARGET_ORG/REPO/teams

# [ ] Branch protections applied
gh api repos/TARGET_ORG/REPO/branches/main/protection

# [ ] Webhooks configured
gh api repos/TARGET_ORG/REPO/hooks

# [ ] GitHub Actions secrets set
gh secret list -R TARGET_ORG/REPO

# [ ] Source archived/deleted
gh api orgs/SOURCE_ORG (should error if deleted)

# [ ] Redirects in place (if applicable)
curl -I https://github.com/SOURCE_ORG/REPO
```

---

## 📚 Resources

- [GitHub CLI Docs: gh repo](https://cli.github.com/manual/gh_repo)
- [GitHub API: Repos](https://docs.github.com/en/rest/repos)
- [GitHub API: Organizations](https://docs.github.com/en/rest/orgs)
- [Git Mirroring](https://git-scm.com/docs/git-clone#--mirror)
- [GitHub Enterprise Administration](https://docs.github.com/en/enterprise-cloud@latest/admin)

---

## 🚫 What Cannot Be Automated

These require manual action via GitHub Web UI:
- [ ] Delete organization (requires owner confirmation)
- [ ] Change org billing plan
- [ ] Invite members to org (if not in target org yet)
- [ ] Transfer org ownership
- [ ] Create organization

---

**Generated:** 2026-05-19T00:08:51Z  
**Status:** Reference guide for ORGANVM architecture  
**Recommendation:** Use Option A (Unified Superproject) to keep structure intact
