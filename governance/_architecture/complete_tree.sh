#!/bin/bash
set -euo pipefail

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

print_tree() {
  local dir="$1"
  local prefix="$2"
  
  # Get subdirectories, excluding hidden ones
  while IFS= read -r subdir; do
    local name=$(basename "$subdir")
    echo "${prefix}├── $name/"
  done < <(find "$dir" -maxdepth 1 -type d ! -name "." ! -name "..*" | sort)
}

cat << 'TREE'
📊 ENTERPRISE STRUCTURE: meta-organvm
=====================================

meta-organvm (Enterprise)
│
├── meta-organvm (Organization)
│   ├── .github
│   ├── meta-organvm--superproject (KEY: Org admin hub)
│   ├── meta-organvm.github.io
│   ├── organvm-scrutator
│   ├── persona-fleet
│   ├── digital-income-organism-inquiry
│   └── _agent-health
│
├── organvm-i-theoria (Organization) — THEORIA (theory/knowledge)
│   ├── .github
│   ├── organvm-i-theoria--superproject
│   │   ├── auto-revision-epistemic-engine
│   │   ├── call-function--ontological
│   │   ├── cognitive-archaelogy-tribunal
│   │   ├── linguistic-atomization-framework
│   │   ├── my-knowledge-base
│   │   ├── narratological-algorithmic-lenses
│   │   ├── nexus--babel-alexandria
│   │   ├── recursive-engine--generative-entity
│   │   ├── sema-metra--alchemica-mundi
│   │   └── studium-generale
│   ├── organvm-i-theoria.github.io
│   ├── prompt-corpvs (KEY: Prompt framework)
│   ├── organvm-corpvs-testamentvm (KEY: IRF + atom registry)
│   ├── hierarchia-mundi
│   ├── styx-behavioral-economics-theory
│   ├── scale-threshold-emergence
│   ├── atomic-substrata
│   ├── vigiles-aeternae--corpus-mythicum
│   ├── conversation-corpus-engine
│   ├── rules-system-bound
│   ├── mesh
│   ├── growth-auditor
│   ├── sovereign--ground
│   └── carrier-wave--zeitgeist-thesis
│
├── organvm-ii-poiesis (Organization) — POIESIS (creation/making)
│   ├── .github
│   ├── organvm-ii-poiesis--superproject
│   │   ├── a-i-council--coliseum
│   │   ├── a-mavs-olevm
│   │   ├── academic-publication
│   │   ├── alchemical-synthesizer
│   │   ├── archive-past-works
│   │   ├── art-from--auto-revision-epistemic-engine
│   │   ├── art-from--narratological-algorithmic-lenses
│   │   ├── artist-toolkit-and-templates
│   │   ├── audio-synthesis-bridge
│   │   ├── case-studies-methodology
│   │   ├── chthon-oneiros
│   │   ├── client-sdk
│   │   ├── core-engine
│   │   ├── docs/
│   │   ├── example-ai-collaboration
│   │   ├── example-choreographic-interface
│   │   ├── example-generative-music
│   │   ├── example-generative-visual
│   │   ├── example-interactive-installation
│   │   ├── example-theatre-dialogue
│   │   ├── ivi374ivi027-05
│   │   ├── krypto-velamen
│   │   ├── learning-resources
│   │   ├── life-betterment-simulation
│   │   ├── MET4
│   │   ├── metasystem-master
│   │   ├── performance-sdk
│   │   ├── shared-remembrance-gateway
│   │   └── showcase-portfolio
│   ├── organvm-ii-poiesis.github.io
│   ├── styx-behavioral-art
│   ├── vigiles-aeternae--theatrum-mundi
│   └── object-lessons
│
├── organvm-iii-ergon (Organization) — ERGON (work/action)
│   ├── .github
│   ├── organvm-iii-ergon--superproject
│   │   ├── classroom-rpg-aetheria
│   │   ├── commerce--meta
│   │   ├── content-engine--asset-amplifier
│   │   ├── docs/
│   │   │   ├── contributions/
│   │   │   └── ...
│   │   ├── life-my--midst--in
│   │   ├── public-record-data-scrapper
│   │   ├── sign-signal--voice-synth
│   │   ├── sovereign-systems--elevate-align
│   │   └── the-actual-news
│   ├── organvm-iii-ergon.github.io
│   ├── specvla-ergon--avditor-mvndi
│   ├── content-engine--asset-amplifier (standalone)
│   ├── sovereign-systems--elevate-align (standalone)
│   ├── sign-signal--voice-synth (standalone)
│   └── sovereign-systems--layer-above-hokage
│
├── organvm-iv-taxis (Organization) — TAXIS (order/arrangement)
│   ├── .github
│   ├── organvm-iv-taxis--superproject
│   ├── organvm-iv-taxis.github.io
│   └── org-dotgithub
│
├── organvm-v-logos (Organization) — LOGOS (word/reason)
│   ├── .github
│   ├── organvm-v-logos--superproject
│   └── organvm-v-logos.github.io
│
├── organvm-vi-koinonia (Organization) — KOINONIA (community/fellowship)
│   ├── .github
│   ├── organvm-vi-koinonia--superproject
│   └── organvm-vi-koinonia.github.io
│
└── organvm-vii-kerygma (Organization) — KERYGMA (proclamation/message)
    ├── .github
    ├── organvm-vii-kerygma--superproject
    └── organvm-vii-kerygma.github.io

=====================================
KEY REPOS (CRITICAL HUBS):
- organvm-corpvs-testamentvm (i-theoria): IRF + atom registry
- prompt-corpvs (i-theoria): prompt framework & atoms
- metasystem-master (ii-poiesis): core AI creation engine
- organvm-iii-ergon--superproject: product/output layer
TREE

