#!/bin/bash

get_full_tree() {
  local owner="$1"
  local repo="$2"
  local depth="${3:-0}"
  local max_depth="${4:-5}"
  local prefix="${5:-}"
  
  if [ $depth -ge $max_depth ]; then
    return
  fi
  
  # Fetch tree from GitHub API
  local tree=$(gh api repos/$owner/$repo/git/trees/HEAD?recursive=1 2>/dev/null | jq -r '.tree[] | select(.type == "tree") | .path' | sort)
  
  if [ -z "$tree" ]; then
    return
  fi
  
  # Parse tree paths and build hierarchy
  declare -A printed
  
  echo "$tree" | while read path; do
    # Skip hidden directories
    if [[ "$path" =~ /\. ]] || [[ "$path" =~ ^\. ]]; then
      continue
    fi
    
    # Count depth
    local path_depth=$(echo "$path" | tr -cd '/' | wc -c)
    
    if [ $((depth + path_depth)) -lt $max_depth ]; then
      # Extract just the folder name at this depth
      local segments=(${path//\// })
      local folder="${segments[$depth]}"
      
      # Only print each unique folder once per level
      if [ ! -z "$folder" ] && [[ "$folder" != "."* ]]; then
        echo "${prefix}├── $folder/"
      fi
    fi
  done | sort | uniq
}

echo "🌳 COMPLETE ORGANVM GITHUB TREE"
echo "================================"
echo ""

# Fetch all orgs
ORGS=$(gh api graphql -f query='{enterprise(slug:"meta-organvm"){organizations(first:100){nodes{login}}}}' 2>/dev/null | jq -r '.data.enterprise.organizations.nodes[].login' | sort)

for ORG in $ORGS; do
  echo ""
  echo "📦 ORGANIZATION: $ORG"
  echo "════════════════════════════════════════════"
  
  # Get all repos in org
  REPOS=$(gh api orgs/$ORG/repos --paginate 2>/dev/null | jq -r '.[].name' | sort)
  
  for REPO in $REPOS; do
    echo ""
    echo "📁 $ORG/$REPO"
    echo "───────────────────────────────────"
    
    # Get tree
    gh api repos/$ORG/$REPO/git/trees/HEAD?recursive=1 2>/dev/null | \
      jq -r '.tree[] | select(.type == "tree") | .path' | \
      grep -v '^\.' | \
      sort | \
      sed 's|^|  |' | \
      head -50
    
  done | head -100
done

