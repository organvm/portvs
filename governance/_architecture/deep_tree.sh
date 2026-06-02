#!/bin/bash
set -euo pipefail

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Function to print directory tree
tree_print() {
  local dir="$1"
  local prefix="$2"
  local indent="${3:- }"
  
  local -a entries
  local count=0
  while IFS= read -r entry; do
    entries+=("$entry")
    ((count++))
  done < <(find "$dir" -maxdepth 1 -type d ! -name ".*" | sort | tail -n +2)
  
  local i=0
  for entry in "${entries[@]}"; do
    ((i++))
    local name=$(basename "$entry")
    if [ $i -eq ${#entries[@]} ]; then
      echo "${prefix}└── $name/"
      local new_prefix="${prefix}    "
    else
      echo "${prefix}├── $name/"
      local new_prefix="${prefix}│   "
    fi
    
    # Recurse one level deeper for key repos
    if [ $(find "$entry" -maxdepth 1 -type d ! -name ".*" | wc -l) -gt 1 ]; then
      tree_print "$entry" "$new_prefix" "" 2>/dev/null || true
    fi
  done
}

echo "🌳 DEEP DIRECTORY STRUCTURE"
echo "============================"
echo ""

# Clone and analyze key repos
REPOS=(
  "meta-organvm/meta-organvm--superproject"
  "organvm-i-theoria/organvm-i-theoria--superproject"
  "organvm-ii-poiesis/organvm-ii-poiesis--superproject"
  "organvm-iii-ergon/organvm-iii-ergon--superproject"
)

for REPO in "${REPOS[@]}"; do
  echo "Fetching: $REPO"
  gh repo clone "$REPO" "$TMPDIR/$REPO" -- --depth 1 2>&1 | grep -v "^Cloning\|^Receiving\|^Resolving" || true
  
  if [ -d "$TMPDIR/$REPO" ]; then
    SAFE_REPO=$(echo "$REPO" | tr '/' '_')
    echo ""
    echo "📁 $REPO"
    echo "────────────────────────────────────────────"
    tree_print "$TMPDIR/$REPO" ""
    echo ""
  fi
done
