#!/bin/bash
set -euo pipefail

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Core repos to map (critical ones with substantial code)
declare -a CORE_REPOS=(
  "meta-organvm/meta-organvm--superproject"
  "organvm-i-theoria/organvm-i-theoria--superproject"
  "organvm-i-theoria/organvm-corpvs-testamentvm"
  "organvm-ii-poiesis/organvm-ii-poiesis--superproject"
  "organvm-iii-ergon/organvm-iii-ergon--superproject"
  "organvm-viii-meta/domus-semper-palingenesis"
)

echo "=== ENTERPRISE: meta-organvm ==="
echo ""

for REPO in "${CORE_REPOS[@]}"; do
  echo "Cloning $REPO (shallow)..."
  gh repo clone "$REPO" "$TMPDIR/$REPO" -- --depth 1 2>&1 | grep -v "Cloning into\|Receiving objects\|Resolving deltas" || true
  
  if [ -d "$TMPDIR/$REPO" ]; then
    echo ""
    echo "📁 $REPO"
    echo "─────────────────────────────────"
    find "$TMPDIR/$REPO" -not -path "*/\.*" -type d | head -30 | sed 's|'"$TMPDIR/$REPO"'||g' | sed 's|^|  |' | sort
    echo ""
  fi
done
