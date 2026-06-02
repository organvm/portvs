---
title: "Git Remote Sync Commands"
date: "2026-05-18T05:43:06 (UTC -04:00)"
source: chatgpt.com
---
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

## Q: 
i want to ensure total data preservation, 100% parity between local & remote w the more current & more improved upon winning; the goal is to lighten local storageShow moreShow less

## A: 
I’ll separate this into two problems: Git parity and storage offloading. The key issue is that “newer wins” conflicts with Git’s normal history model unless you define a sync policy.

You do **not** want `git push --mirror` as your default. You want a **preservation-first sync pipeline**:

```plain text
git statusgit pull --rebase --autostash origin maingit add -Agit commit -m "SYNC :: $(date '+%Y-%m-%d_%H-%M-%S')" || truegit push origin maingit push --follow-tagsgit lfs push --all origin
```

This means:

```plain text
remote changes come down firstlocal improvements are replayed on topall local changes are committedremote receives the improved statelarge files tracked by LFS are uploaded
```

## But for “100% data preservation”

Git alone is not enough.

Use this architecture:

```plain text
LOCAL_ACTIVE  = only current working filesREMOTE_GIT  = code, text, manifests, version historyGIT_LFS  = large project assetsCLOUD_ARCHIVE / OBJECT_STORAGE  = heavy media, exports, datasets, raw capturesLOCAL_CACHE  = disposable local copies
```

Your local machine should become a **working cache**, not the canonical archive.

## The command set I’d actually use

### 1. Normal daily sync

```plain text
git pull --rebase --autostash origin maingit add -Agit commit -m "SYNC :: $(date '+%Y-%m-%d_%H-%M-%S')" || truegit push origin maingit push --follow-tagsgit lfs push --all origin
```

### 2. Full preservation snapshot

```plain text
git bundle create "../$(basename "$PWD")_FULL_$(date '+%Y-%m-%d_%H-%M-%S').bundle" --all
```

This creates a portable full Git archive.

### 3. Clean local after remote is verified

```plain text
git fetch origingit statusgit lfs fsckgit gc --prune=now
```

For LFS files, after verifying they are remote:

```plain text
git lfs prune
```

## Best alias

```plain text
alias gpreserve='git pull --rebase --autostash origin main && git add -A && git commit -m "SYNC :: $(date "+%Y-%m-%d_%H-%M-%S")" || true && git push origin main && git push --follow-tags && git lfs push --all origin'
```

## Rule

Use Git for:

```plain text
codetextmarkdownmanifestsconfigssmall structured files
```

Use Git LFS / cloud archive for:

```plain text
videoaudioimagesdatasetsexportszipslarge binaries
```

## The clean doctrine

```plain text
REMOTE IS CANONICALLOCAL IS WORKSPACECACHE IS DISPOSABLEMANIFESTS VERIFY PARITY
```

The next upgrade is to create a repo-level `MANIFEST.sha256` so every file has a checksum before you delete local copies.

## Q: 
create a repo-level MANIFEST.sha256 so every file has a checksum before you delete local copies.Show moreShow less

## A: 
Use this from the repo root:

```plain text
find . \  -type f \  ! -path './.git/*' \  ! -name 'MANIFEST.sha256' \  -print0 \| sort -z \| xargs -0 shasum -a 256 \> MANIFEST.sha256
```

Verify later:

```plain text
shasum -a 256 -c MANIFEST.sha256
```

Commit the manifest:

```plain text
git add MANIFEST.sha256git commit -m "ADD :: repo checksum manifest"git push origin main
```

Best reusable alias:

```plain text
alias manifest256='find . -type f ! -path "./.git/*" ! -name "MANIFEST.sha256" -print0 | sort -z | xargs -0 shasum -a 256 > MANIFEST.sha256'
```

Then your preservation sequence becomes:

```plain text
manifest256shasum -a 256 -c MANIFEST.sha256git add -Agit commit -m "SYNC :: manifest verified :: $(date '+%Y-%m-%d_%H-%M-%S')"git push origin main
```

For macOS, `shasum -a 256` is the safest default.

