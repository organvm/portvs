---
title: "Git Remote Sync Commands"
date: "2026-05-18T14:14:40 (UTC -04:00)"
source: chatgpt.com
---
## Q: 
for ensuring all local is on remote 100%, instead of stage all, commit all, origin push; what should i command?Show moreShow less

## A: 
If your actual goal is:

> “Guarantee the remote becomes an exact mirror of local state.”

…then `git add . && git commit && git push` is not sufficient.

That sequence only pushes:

*   tracked changes
    
*   committed changes
    
*   current branch state
    

It does **not** guarantee:

*   deleted remote branches are removed
    
*   tags are synchronized
    
*   untracked files are handled
    
*   ignored/generated artifacts are excluded correctly
    
*   remote history matches local exactly
    
*   LFS objects are uploaded
    
*   submodules are synchronized
    

The proper approach depends on what “100%” means operationally.

# 1. Standard Safe Full Sync (recommended)

For most repositories:

```plain text
git add -Agit commit -m "SYNC :: $(date '+%Y-%m-%d_%H-%M-%S')"git push --allgit push --tags
```

`git add -A`

*   stages:
    
    *   modified
        
    *   deleted
        
    *   renamed
        
    *   new tracked files
        

Better than `git add .`

Then:

```plain text
git push --all
```

pushes all local branches.

Then:

```plain text
git push --tags
```

syncs tags.

* * *

# 2. Exact Mirror Mode (dangerous but true mirror)

If you want remote == local exactly:

```plain text
git push --mirror
```

This:

*   pushes all refs
    
*   deletes remote refs not existing locally
    
*   mirrors branches/tags/refs completely
    

This is the closest thing to:

> “make remote identical to local”

But:

*   dangerous on shared repos
    
*   can erase remote branches/history
    

Use mainly for:

*   backup repos
    
*   personal infra
    
*   canonical mirrors
    

* * *

# 3. True Repository Preservation Workflow

If your concern is:

> “I never want local work lost”

Then Git alone is insufficient.

You also need:

## A. LFS sync (if using large files)

```plain text
git lfs push --all origin
```

Otherwise remote may miss binaries.

* * *

## B. Verify remote integrity

```plain text
git fetch --allgit statusgit fsck
```

* * *

## C. Push with upstream tracking

First push:

```plain text
git push -u origin main
```

Then future pushes simpler.

* * *

# 4. Your likely desired canonical command

Given your OS/repository architecture discussions, you probably want:

```plain text
git add -A && \git commit -m "SYNC :: $(date '+%Y-%m-%d_%H-%M-%S')" && \git push --all && \git push --tags
```

Alias example:

```plain text
alias gsyn='git add -A && git commit -m "SYNC :: $(date "+%Y-%m-%d_%H-%M-%S")" && git push --all && git push --tags'
```

* * *

# 5. If you mean “snapshot entire working directory”

Git is not enough.

Git ignores:

*   `.gitignore`
    
*   system files
    
*   permissions nuances
    
*   external assets
    
*   databases
    
*   symlink targets
    
*   hidden metadata
    

Then you need layered backup architecture:

```plain text
LOCAL_WORKSPACE    ↓GIT_REPO    ↓REMOTE_GIT    ↓ARCHIVE_SNAPSHOT    ↓COLD_STORAGE
```

Meaning:

*   GitHub = version graph
    
*   rsync/restic/zfs/tar = actual preservation layer
    

* * *

# 6. Best-practice modern sync command

Practical professional default:

```plain text
git add -A && \git commit -m "SYNC" || true && \git push --follow-tags
```

`|| true`  
prevents failure if nothing changed.

`--follow-tags`  
pushes annotated tags tied to commits.

* * *

# 7. Highest-integrity personal workflow

For your kind of archival/systemic practice:

```plain text
git statusgit add -Agit commitgit push --allgit push --tagsgit lfs push --all origin
```

Then periodic:

```plain text
git bundle create FULL_BACKUP.bundle --all
```

That creates a portable full-repository archive independent of GitHub.

This is materially closer to:

> “100% local preserved remotely”  
> than ordinary push workflows.

## A: 
Use this handoff prompt:

```plain text
You are operating inside a local Git repository.Goal:Ensure total data preservation and remote parity before any local files are deleted or offloaded.Doctrine:REMOTE IS CANONICAL.LOCAL IS WORKSPACE.CACHE IS DISPOSABLE.MANIFESTS VERIFY PARITY.Tasks:1. Inspect the repo state.2. Create or update a repo-level MANIFEST.sha256 containing SHA-256 checksums for every file except:   - .git/*   - MANIFEST.sha256 itself3. Verify MANIFEST.sha256 passes locally.4. Stage all changes, including deletions and the manifest.5. Commit with a timestamped sync message.6. Pull/rebase safely if needed.7. Push to origin/main.8. Push tags.9. If Git LFS is present, push all LFS objects.10. Fetch from origin and confirm local HEAD matches origin/main.11. Do not delete local files until verification succeeds.12. Output the exact commands run and the final verification status.Preferred macOS commands:find . \  -type f \  ! -path './.git/*' \  ! -name 'MANIFEST.sha256' \  -print0 \| sort -z \| xargs -0 shasum -a 256 \> MANIFEST.sha256shasum -a 256 -c MANIFEST.sha256git pull --rebase --autostash origin maingit add -Agit commit -m "SYNC :: manifest verified :: $(date '+%Y-%m-%d_%H-%M-%S')" || truegit push origin maingit push --follow-tagsif command -v git-lfs >/dev/null 2>&1; then  git lfs push --all originfigit fetch origingit statusgit rev-parse HEADgit rev-parse origin/mainSuccess condition:HEAD and origin/main resolve to the same commit hash, MANIFEST.sha256 verifies cleanly, and no uncommitted changes remain unless explicitly documented.
```

More aggressive “agent mode” version:

```plain text
Act as a preservation-first Git synchronization agent.Do not optimize for speed. Optimize for non-loss, auditability, and reversibility.Before any cleanup or deletion:- create MANIFEST.sha256- verify all checksums- commit all repo-state changes- push to origin/main- push tags- push Git LFS objects if present- confirm local HEAD equals origin/main- report any ignored, untracked, oversized, or non-Git-preserved filesNever assume git push alone means full preservation.Never delete local copies unless checksum verification and remote parity are both confirmed.If conflicts occur:- stop- explain the conflict- preserve both versions where possible- do not choose destructively without explicit instructionFinal output must include:- commands run- files excluded from manifest- commit hash- origin/main hash- LFS status- remaining risks- deletion/offload readiness: YES or NO
```

## Q: 
provide as template w env variables & no hardcoded dynamic elementsShow moreShow less

## A: 
```plain text
#!/usr/bin/env bash# ==============================================================================# ::REPO_PRESERVE_SYNC_TEMPLATE::# ==============================================================================## PURPOSE:# Preservation-first repository synchronization template.## PRINCIPLES:# REMOTE_IS_CANONICAL# LOCAL_IS_WORKSPACE# CACHE_IS_DISPOSABLE# MANIFESTS_VERIFY_PARITY## REQUIREMENTS:# - git# - shasum# - optional: git-lfs## ==============================================================================set -Eeuo pipefail# ==============================================================================# ENVIRONMENT VARIABLES# ==============================================================================export REPO_ROOT="${REPO_ROOT:-$(pwd)}"export REMOTE_NAME="${REMOTE_NAME:-origin}"export PRIMARY_BRANCH="${PRIMARY_BRANCH:-main}"export MANIFEST_NAME="${MANIFEST_NAME:-MANIFEST.sha256}"export HASH_ALGORITHM="${HASH_ALGORITHM:-256}"export COMMIT_PREFIX="${COMMIT_PREFIX:-SYNC}"export COMMIT_CONTEXT="${COMMIT_CONTEXT:-manifest_verified}"export ENABLE_LFS_PUSH="${ENABLE_LFS_PUSH:-true}"export ENABLE_BUNDLE_EXPORT="${ENABLE_BUNDLE_EXPORT:-true}"export BUNDLE_OUTPUT_DIR="${BUNDLE_OUTPUT_DIR:-../_REPO_BUNDLES}"export EXCLUDE_PATHS="${EXCLUDE_PATHS:-./.git/*}"export VERIFY_REMOTE_PARITY="${VERIFY_REMOTE_PARITY:-true}"# ==============================================================================# DERIVED VARIABLES# ==============================================================================export TIMESTAMP="${TIMESTAMP:-$(date '+%Y-%m-%d_%H-%M-%S')}"export COMMIT_MESSAGE="${COMMIT_MESSAGE:-${COMMIT_PREFIX} :: ${COMMIT_CONTEXT} :: ${TIMESTAMP}}"export BUNDLE_NAME="${BUNDLE_NAME:-$(basename "$REPO_ROOT")_${TIMESTAMP}.bundle}"export LOCAL_HEAD_HASH=""export REMOTE_HEAD_HASH=""# ==============================================================================# FUNCTIONS# ==============================================================================generate_manifest() {  find "$REPO_ROOT" \    -type f \    ! -path "$EXCLUDE_PATHS" \    ! -name "$MANIFEST_NAME" \    -print0 \  | sort -z \  | xargs -0 shasum -a "$HASH_ALGORITHM" \  > "$REPO_ROOT/$MANIFEST_NAME"}verify_manifest() {  (    cd "$REPO_ROOT"    shasum -a "$HASH_ALGORITHM" -c "$MANIFEST_NAME"  )}sync_remote() {  (    cd "$REPO_ROOT"    git pull \      --rebase \      --autostash \      "$REMOTE_NAME" \      "$PRIMARY_BRANCH"  )}stage_changes() {  (    cd "$REPO_ROOT"    git add -A  )}commit_changes() {  (    cd "$REPO_ROOT"    git commit \      -m "$COMMIT_MESSAGE" \    || true  )}push_primary_branch() {  (    cd "$REPO_ROOT"    git push \      "$REMOTE_NAME" \      "$PRIMARY_BRANCH"  )}push_tags() {  (    cd "$REPO_ROOT"    git push \      --follow-tags  )}push_lfs_objects() {  if [[ "$ENABLE_LFS_PUSH" != "true" ]]; then    return  fi  if command -v git-lfs >/dev/null 2>&1; then    (      cd "$REPO_ROOT"      git lfs push \        --all \        "$REMOTE_NAME"    )  fi}create_bundle_backup() {  if [[ "$ENABLE_BUNDLE_EXPORT" != "true" ]]; then    return  fi  mkdir -p "$BUNDLE_OUTPUT_DIR"  (    cd "$REPO_ROOT"    git bundle create \      "${BUNDLE_OUTPUT_DIR}/${BUNDLE_NAME}" \      --all  )}verify_remote_parity() {  if [[ "$VERIFY_REMOTE_PARITY" != "true" ]]; then    return  fi  (    cd "$REPO_ROOT"    git fetch "$REMOTE_NAME"    export LOCAL_HEAD_HASH="$(git rev-parse HEAD)"    export REMOTE_HEAD_HASH="$(git rev-parse "${REMOTE_NAME}/${PRIMARY_BRANCH}")"    echo "LOCAL_HEAD_HASH=${LOCAL_HEAD_HASH}"    echo "REMOTE_HEAD_HASH=${REMOTE_HEAD_HASH}"    if [[ "$LOCAL_HEAD_HASH" != "$REMOTE_HEAD_HASH" ]]; then      echo "ERROR :: REMOTE PARITY FAILED"      exit 1    fi    git status  )}# ==============================================================================# EXECUTION PIPELINE# ==============================================================================echo "BEGIN :: PRESERVATION_SYNC"sync_remotegenerate_manifestverify_manifeststage_changescommit_changespush_primary_branchpush_tagspush_lfs_objectscreate_bundle_backupverify_remote_parityecho "COMPLETE :: PRESERVATION_SYNC"
```

## Q: 
provide as template w env variables & no hardcoded dynamic elements And instead of leading me towards a specific answer, you suggest many possible ones that the universal system will decide based on whose system you're in.Show moreShow less

## A: 
```plain text
::PRESERVATION_SYNC_HANDOFF_TEMPLATE::You are operating inside an unknown repository, workspace, or agent environment.Your task is not to assume a specific toolchain, branch, remote, storage provider, or workflow.Your task is to infer the correct preservation strategy from the environment, using environment variables wherever possible, and present multiple valid implementation paths before selecting the safest one for the current system.────────────────────────────────────────CORE OBJECTIVE────────────────────────────────────────Ensure total data preservation, remote parity, checksum verification, and safe local storage reduction.The desired doctrine is:REMOTE_IS_CANONICALLOCAL_IS_WORKSPACECACHE_IS_DISPOSABLEMANIFESTS_VERIFY_PARITYCURRENT_AND_IMPROVED_STATE_WINSDESTRUCTIVE_ACTIONS_REQUIRE_VERIFIED_PARITY────────────────────────────────────────DO NOT HARDCODE────────────────────────────────────────Do not hardcode:REPO_ROOTREMOTE_NAMEPRIMARY_BRANCHMANIFEST_NAMEHASH_ALGORITHMCOMMIT_MESSAGETIMESTAMPBUNDLE_OUTPUT_DIRARCHIVE_REMOTELFS_PROVIDEROBJECT_STORAGE_PROVIDERPACKAGE_MANAGERCI_PROVIDERSHELL_TYPEOPERATING_SYSTEMUSERNAMEHOME_DIRECTORYPROJECT_NAMEUse environment variables, discovery commands, config files, or interactive-safe defaults.All dynamic values must come from:$REPO_ROOT$REMOTE_NAME$PRIMARY_BRANCH$MANIFEST_NAME$HASH_ALGORITHM$COMMIT_PREFIX$COMMIT_CONTEXT$TIMESTAMP$BUNDLE_OUTPUT_DIR$ARCHIVE_REMOTE$ENABLE_LFS$ENABLE_BUNDLE$ENABLE_REMOTE_VERIFY$ENABLE_OBJECT_ARCHIVE$EXCLUDE_PATHS$INCLUDE_UNTRACKED$DRY_RUN$DELETE_AFTER_VERIFYIf a variable is missing, infer it from the current system and report the inference.────────────────────────────────────────DECISION MODEL────────────────────────────────────────Before executing anything, evaluate which preservation model fits the current system.Possible models include:MODEL_GIT_ONLYFor text, code, configs, manifests, small structured assets.MODEL_GIT_LFSFor repositories with large binaries, media, datasets, design files, audio, video, or generated artifacts that still need version association.MODEL_GIT_PLUS_BUNDLEFor full Git history preservation independent of the hosting provider.MODEL_GIT_PLUS_OBJECT_STORAGEFor heavy files that should not live in Git or Git LFS.MODEL_CLOUD_CANONICALFor systems where Dropbox, Google Drive, iCloud, S3, Backblaze, rsync.net, or another storage layer is the canonical archive.MODEL_MANIFEST_ONLYFor directory trees that are not Git repositories but still need checksum verification.MODEL_HYBRID_ARCHIVEFor mixed creative/code/media repositories requiring Git, LFS, bundle, manifest, and cloud archive together.Do not force one answer.Choose based on the environment.────────────────────────────────────────REQUIRED ANALYSIS────────────────────────────────────────Inspect the current environment and determine:Is this a Git repository?What is $REPO_ROOT?What remotes exist?What is the active branch?What is the upstream branch?Are there untracked files?Are there ignored files that may contain preservation-relevant data?Are there large files?Is Git LFS installed?Is Git LFS configured?Are there submodules?Are there nested repositories?Are there symlinks?Are there generated build folders?Are there media/archive/data folders?Are there files excluded by .gitignore that should be preserved elsewhere?Is there already a manifest?Is there already a bundle/archive/export policy?Is local storage reduction safe?────────────────────────────────────────OUTPUT REQUIREMENTS────────────────────────────────────────Return:SYSTEM_DISCOVERYDetected values for all relevant environment variables.POSSIBLE_STRATEGIESSeveral valid preservation strategies for this system.RECOMMENDED_STRATEGYThe safest strategy based on detected evidence.COMMAND_PLANCommands using environment variables only.RISK_REGISTERAnything that may prevent 100% preservation.PARITY_CRITERIAExact success conditions.DELETE_OR_OFFLOAD_READINESSYES or NO, with reason.────────────────────────────────────────COMMAND TEMPLATE────────────────────────────────────────Use commands shaped like this, adapting only through variables:export REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"export REMOTE_NAME="${REMOTE_NAME:-$(git -C "$REPO_ROOT" remote 2>/dev/null | head -n 1)}"export PRIMARY_BRANCH="${PRIMARY_BRANCH:-$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null)}"export MANIFEST_NAME="${MANIFEST_NAME:-MANIFEST.sha256}"export HASH_ALGORITHM="${HASH_ALGORITHM:-256}"export TIMESTAMP="${TIMESTAMP:-$(date '+%Y-%m-%d_%H-%M-%S')}"export COMMIT_PREFIX="${COMMIT_PREFIX:-SYNC}"export COMMIT_CONTEXT="${COMMIT_CONTEXT:-manifest_verified}"export COMMIT_MESSAGE="${COMMIT_MESSAGE:-$COMMIT_PREFIX :: $COMMIT_CONTEXT :: $TIMESTAMP}"export BUNDLE_OUTPUT_DIR="${BUNDLE_OUTPUT_DIR:-$REPO_ROOT/../_REPO_BUNDLES}"export ENABLE_LFS="${ENABLE_LFS:-auto}"export ENABLE_BUNDLE="${ENABLE_BUNDLE:-true}"export ENABLE_REMOTE_VERIFY="${ENABLE_REMOTE_VERIFY:-true}"export ENABLE_OBJECT_ARCHIVE="${ENABLE_OBJECT_ARCHIVE:-false}"export DRY_RUN="${DRY_RUN:-true}"export DELETE_AFTER_VERIFY="${DELETE_AFTER_VERIFY:-false}"cd "$REPO_ROOT"find "$REPO_ROOT" \  -type f \  ! -path "$REPO_ROOT/.git/*" \  ! -name "$MANIFEST_NAME" \  -print0 \| sort -z \| xargs -0 shasum -a "$HASH_ALGORITHM" \> "$REPO_ROOT/$MANIFEST_NAME"shasum -a "$HASH_ALGORITHM" -c "$REPO_ROOT/$MANIFEST_NAME"git -C "$REPO_ROOT" status --shortgit -C "$REPO_ROOT" pull --rebase --autostash "$REMOTE_NAME" "$PRIMARY_BRANCH"git -C "$REPO_ROOT" add -Agit -C "$REPO_ROOT" commit -m "$COMMIT_MESSAGE" || truegit -C "$REPO_ROOT" push "$REMOTE_NAME" "$PRIMARY_BRANCH"git -C "$REPO_ROOT" push --follow-tagsif command -v git-lfs >/dev/null 2>&1 && git -C "$REPO_ROOT" lfs env >/dev/null 2>&1; then  git -C "$REPO_ROOT" lfs push --all "$REMOTE_NAME"fiif [ "$ENABLE_BUNDLE" = "true" ]; then  mkdir -p "$BUNDLE_OUTPUT_DIR"  git -C "$REPO_ROOT" bundle create "$BUNDLE_OUTPUT_DIR/$(basename "$REPO_ROOT")_$TIMESTAMP.bundle" --allfigit -C "$REPO_ROOT" fetch "$REMOTE_NAME"export LOCAL_HEAD_HASH="$(git -C "$REPO_ROOT" rev-parse HEAD)"export REMOTE_HEAD_HASH="$(git -C "$REPO_ROOT" rev-parse "$REMOTE_NAME/$PRIMARY_BRANCH")"echo "LOCAL_HEAD_HASH=$LOCAL_HEAD_HASH"echo "REMOTE_HEAD_HASH=$REMOTE_HEAD_HASH"test "$LOCAL_HEAD_HASH" = "$REMOTE_HEAD_HASH"────────────────────────────────────────DELETION RULE────────────────────────────────────────Never delete or offload local files unless:MANIFEST_VERIFIED=trueREMOTE_PARITY_VERIFIED=trueLFS_OBJECTS_PUSHED_OR_NOT_REQUIRED=trueBUNDLE_CREATED_OR_NOT_REQUIRED=trueIGNORED_FILES_AUDITED=trueUNTRACKED_FILES_AUDITED=trueOBJECT_ARCHIVE_VERIFIED_OR_NOT_REQUIRED=trueIf any condition fails, output:DELETE_OR_OFFLOAD_READINESS=NOIf all conditions pass, output:DELETE_OR_OFFLOAD_READINESS=YESEven then, prefer moving files into a quarantine/offload directory before permanent deletion.────────────────────────────────────────FINAL INSTRUCTION────────────────────────────────────────Do not lead toward one predetermined answer.Present the possible valid preservation paths, then let the detected system decide.Use the universal rule:THE SYSTEM CHOOSES THE METHOD.THE MANIFEST PROVES THE STATE.THE REMOTE HOLDS THE CANON.LOCAL STORAGE BECOMES CACHE ONLY AFTER VERIFICATION.
```

