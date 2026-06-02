#!/usr/bin/env bash
set +e

survey_repo() {
  local repo="$1"
  local cd_ok status_lines ahead behind branch remote_url has_remote dirty_status sync_status
  cd "$repo" 2>/dev/null || { echo "$repo|UNREADABLE|||"; return; }

  branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "DETACHED")
  remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
  has_remote="NO"
  [[ -n "$remote_url" ]] && has_remote="YES"

  status_lines=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  dirty_status="CLEAN"
  [[ "$status_lines" -gt 0 ]] && dirty_status="DIRTY:$status_lines"

  sync_status="UNKNOWN"
  if [[ "$has_remote" == "YES" ]] && [[ "$branch" != "DETACHED" ]]; then
    local upstream
    upstream=$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null)
    if [[ -n "$upstream" ]]; then
      ahead=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "?")
      behind=$(git rev-list --count "HEAD..@{u}" 2>/dev/null || echo "?")
      if [[ "$ahead" == "0" && "$behind" == "0" ]]; then
        sync_status="PARITY"
      elif [[ "$ahead" != "0" && "$behind" == "0" ]]; then
        sync_status="AHEAD:$ahead"
      elif [[ "$ahead" == "0" && "$behind" != "0" ]]; then
        sync_status="BEHIND:$behind"
      else
        sync_status="DIVERGED:a$ahead/b$behind"
      fi
    else
      sync_status="NO_UPSTREAM"
    fi
  fi

  echo "$repo|$branch|$dirty_status|$sync_status|$has_remote"
}

REPOS=$(
  find ~/Workspace -maxdepth 4 -name .git -type d 2>/dev/null | sed 's|/.git$||'
  find ~/Code/organvm -maxdepth 3 -name .git -type d 2>/dev/null | sed 's|/.git$||'
)

printf "%-70s | %-20s | %-12s | %-18s | %s\n" "REPO" "BRANCH" "DIRTY" "SYNC" "HAS_REMOTE"
printf "%-70s-+-%-20s-+-%-12s-+-%-18s-+-%s\n" "----------------------------------------------------------------------" "--------------------" "------------" "------------------" "----------"

echo "$REPOS" | while read -r r; do
  [[ -z "$r" ]] && continue
  survey_repo "$r" | while IFS='|' read -r repo branch dirty sync hasremote; do
    short=$(echo "$repo" | sed "s|$HOME|~|")
    printf "%-70s | %-20s | %-12s | %-18s | %s\n" "$short" "$branch" "$dirty" "$sync" "$hasremote"
  done
done
