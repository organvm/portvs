#!/bin/bash
set -euo pipefail

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Function to recursively print tree with limited depth
print_tree() {
  local dir="$1"
  local prefix="$2"
  local max_depth="${3:-4}"
  local current_depth="${4:-0}"
  
  if [ $current_depth -ge $max_depth ]; then
    return
  fi
  
  local -a entries
  while IFS= read -r entry; do
    if [ ! -d "$entry" ]; then
      continue
    fi
    local name=$(basename "$entry")
    if [[ "$name" == "."* ]]; then
      continue
    fi
    entries+=("$entry")
  done < <(find "$dir" -maxdepth 1 -type d ! -name "." | sort)
  
  local count=${#entries[@]}
  local i=0
  
  for entry in "${entries[@]}"; do
    ((i++))
    local name=$(basename "$entry")
    local is_last=$((i == count ? 1 : 0))
    
    if [ $is_last -eq 1 ]; then
      echo "${prefix}└── $name/"
      local new_prefix="${prefix}    "
    else
      echo "${prefix}├── $name/"
      local new_prefix="${prefix}│   "
    fi
    
    # Recurse deeper
    local sub_count=$(find "$entry" -maxdepth 1 -type d ! -name ".*" ! -name "$entry" | wc -l)
    if [ $sub_count -gt 0 ]; then
      print_tree "$entry" "$new_prefix" "$max_depth" $((current_depth + 1)) 2>/dev/null || true
    fi
  done
}

# Main repos to traverse
declare -a REPOS=(
  "meta-organvm/meta-organvm--superproject"
  "organvm-i-theoria/organvm-i-theoria--superproject"
  "organvm-ii-poiesis/organvm-ii-poiesis--superproject"
  "organvm-iii-ergon/organvm-iii-ergon--superproject"
  "organvm-iv-taxis/organvm-iv-taxis--superproject"
)

echo "🌳 COMPLETE ORGANVM FOLDER TREE (5-LEVEL DEPTH)"
echo "=================================================="
echo ""

for REPO in "${REPOS[@]}"; do
  REPO_SHORT=$(basename "$REPO")
  CLONE_PATH="$TMPDIR/$REPO_SHORT"
  
  echo "Cloning $REPO..."
  gh repo clone "$REPO" "$CLONE_PATH" -- --depth 1 2>&1 | grep -E "Cloning|fatal" || true
  
  if [ -d "$CLONE_PATH" ]; then
    echo ""
    echo "📦 $REPO"
    echo "════════════════════════════════════════════"
    print_tree "$CLONE_PATH" "" 5 0
    echo ""
    echo ""
  else
    echo "⚠️  Could not clone $REPO"
    echo ""
  fi
done

