#!/usr/bin/env bash
# Reset AGENTS.md, CLAUDE.md, GEMINI.md in repos where they're the ONLY modified files
# (preserves any repo with real work mixed in)

reset_if_trio_only() {
  local repo="$1"
  cd "$repo" 2>/dev/null || return

  # Get the list of modified files
  local modified
  modified=$(git status --porcelain | awk '{print $2}' | sort)

  # Expected trio (sorted)
  local expected=$'AGENTS.md\nCLAUDE.md\nGEMINI.md'

  if [[ "$modified" == "$expected" ]]; then
    git checkout -- AGENTS.md CLAUDE.md GEMINI.md 2>/dev/null
    echo "RESET: $repo"
  fi
}

REPOS=$(
  find ~/Workspace -maxdepth 4 -name .git -type d 2>/dev/null | sed 's|/.git$||'
  find ~/Code/organvm -maxdepth 3 -name .git -type d 2>/dev/null | sed 's|/.git$||'
)

echo "$REPOS" | while read -r r; do
  [[ -z "$r" ]] && continue
  reset_if_trio_only "$r"
done
