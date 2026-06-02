#!/bin/bash

# Fetch git tree for a repo
get_tree() {
  local owner="$1"
  local repo="$2"
  
  echo "📁 $owner/$repo"
  echo "────────────────────────────────────"
  
  gh api repos/$owner/$repo/git/trees/HEAD \
    --jq '.tree[] | select(.type == "tree") | .path' 2>/dev/null | \
    head -40 | sed 's|^|  ├── |'
  
  echo ""
}

echo "🌳 GITHUB ENTERPRISE FOLDER STRUCTURE"
echo "======================================="
echo ""

# Key repos with substantial folder hierarchies
get_tree "meta-organvm" "meta-organvm--superproject"
get_tree "organvm-i-theoria" "organvm-i-theoria--superproject"
get_tree "organvm-ii-poiesis" "organvm-ii-poiesis--superproject"
get_tree "organvm-iii-ergon" "organvm-iii-ergon--superproject"
get_tree "organvm-iv-taxis" "organvm-iv-taxis--superproject"

