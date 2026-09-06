# Visual-Form Evolutionary Audit — 2026-09-05

Status: evidence reconciliation after the Artifact 001 execution tranche.
Owner/boundary: Portvs, `incubator/triptych-video-canon/`.
Coordination: issue #8; audit PR #7; implementation PR #9.

This updates the existing audit rather than starting another census or archaeology project. The previous broad model and roadmap remain in Git history at `95842ae8f45a4b00f630ad12054c845aa67f30c0`; their proposed capabilities were not execution evidence. The current implementation evidence is PR #9 commit `1009628e58563bb1b20771bfbe69fe573d31adbf` and its `ARTIFACT_001_RECEIPT.md`.

## Evidence vocabulary

Keep `verified`, `documented` and `user-attested` attached to individual claims. Record inspection stage separately:

`located in metadata -> original bytes retrieved/hashed -> structural inspection -> visual inspection -> executed/rendered`

Connector-extracted text is an additional text-inspection stage, not a substitute for original bytes or preserved structural relationships. An archived tree proves what was listed, not that every dependency remains reachable. Sequence names and blank descriptive CSV columns do not specify a composition. Do not promote an entire work because one locator is verified.

The works below form a provisional lineage network. Direct chronological derivation between Triptych, Up the Hill Backwards, Floating Points and Danse has not been established.

## Reconciled lineage and recovery matrix

| Object | Supported claim / stage | Unverified boundary |
|---|---|---|
| Triptych Video Canon in Portvs | Renderer source inspected at main `48da3da293ecd7604b6c9d3ce19d0bf49a70013d`; original blob `6155fa1b8c9d5284c3deda0eaf56b342e47cf1bc`; synthetic baseline executed and visually inspected; five legacy decoded-output regressions passed | This renderer is not automatically the earlier photo selector; complete website/export workflow was not executed in this tranche |
| Earlier tri-panel photo selector / First Circle | Artist testimony and related records document a prior work | Exact implementation, identity and relation to later versions remain unresolved |
| Archival TripTicks | A MOV locator exists in Dropbox metadata; prior records separately mention a local MP4 | Original bytes, playback and MOV/MP4 equivalence not verified; do not conflate either with the selector, later renderer or conceptual TRIPTYCH record |
| Floating Points | V1/V2/V3 project locators documented; prior sequence CSV and archived tree inspected as text. V1 now yielded connector-extracted project text containing `floating_points_V1_SEQ`, dependency references and `AE.ADBE Opacity` identifiers | No original-byte hash, XML/object graph parse, track/layer count, geometry, blend/mask/keyframe reconstruction, complete assets or Premiere playback verified. Artist's approximately 50–100 layers remains user-attested |
| Up the Hill Backwards | Known MP4 and Ableton/project-directory locators; MP4 download-link metadata resolved in this tranche. Quad composition remains artist-attested | Media bytes and representative frames not retrieved; visual timing/topology, exact Premiere source and dependencies remain unverified. Ableton alone does not establish visual topology |
| Narcissus | Audiovisual references documented; similarly named MET4 PDF located previously | Canonical audiovisual source and relationship to that PDF unresolved; do not treat PDF similarity as identity |
| iPhone photo-widget compositions | Artist testimony and earlier supplied visual examples support independently changing image-bank juxtaposition as an aesthetic reference | Not an executed compatibility fixture for the new engine |
| The Thing Without a Name / Danse macabre | Prior repository inspection documented deterministic `f(seed,t)` architecture, still-photo/spatial concepts and lineage records | No particular behavior was revalidated or imported in this tranche. No blanket compatibility, direct-ancestor or most-advanced-proven claim follows from a plan |
| Visualizer, web/3D and exhibit branches | Existing Visual Form Canon inventories document candidate runtimes and promotion destinations | Inventory evidence is not new execution, current runtime validation, ownership selection or proof of a complete installation |

Raw private locators, personal paths, media and temporary URLs are not publication metadata and are intentionally excluded from this audit. Archive originals were not modified.

## Formal hypotheses versus implementation

The reusable hypotheses remain simultaneous apertures, independent clocks, chance conjunction, layered/nested imagery, deterministic state, spatial planes and multiple render targets. Not all are implemented or historically verified. In particular, dense nesting, opacity/blend graphs, generative audio, modulation, navigable 3D, mocap and physical installation remain later extensions.

Preserve originals first; produce a formal analysis and evidenced compatibility description before calling a descendant historically faithful. A synthetic quad is an engineering fixture, not a recovered Up the Hill Backwards composition.

## Current executable result: Artifact 001

The artist's amendment requires N panels to represent N independent loop instances. Each supported count/variant requires an explicit portrait/landscape design; source reuse must be explicit, never automatic filler. Orientation is presentation, not a reset of content or time.

PR #9's existing 3/4/5/6-loop authoring model and eight explicit layouts were retained. A small strict-state compiler now feeds the existing Triptych `Panel`/`Segment` rendering/encoding path; it is not a second per-count rendering application. Legacy CLI scheduling is retained behind its compatibility path. The adapter accepts initial resolved-source authoring snapshots and explicitly rejects untranslated old event histories.

Executed evidence:

- Original synthetic Triptych baseline, including fixed/clip timing and none/panel/mix audio samples.
- 38 passing narrow tests, including deterministic replay, independent clocks, malformed states, absent/altered media, every active loop mapped once, orientation-independent state and a real still/hold render.
- 360 exact legacy segment-command comparisons and five complete decoded-output regressions.
- Eight six-second H.264 reference renders: 3, 4, 5 and 6 loops, portrait 1080x1920 and landscape 1920x1080; each 24 fps / 144 frames, with reference PNGs.
- A ninth still/video/control render, plus visual inspection of layouts and sampled transitions. Exact commands, source hashes, media facts and output hashes accompany the delivered execution bundle and implementation receipt.

The legacy fixed/mix sample retains an observed timing quirk: 123 video frames and 5.145996-second container duration for a nominal five-second schedule. This is documented, not silently corrected. New schema-1 loop exports are silent; legacy audio behavior is preserved. Generative/routing audio, overlap/masks/depth and unsupported capabilities fail rather than masquerade as implemented features.

Model-level portrait/landscape/portrait continuity and representative viewport geometry were tested. Live browser switching, device playback and resource capacity were not. Numeric resource guards do not demonstrate unrestricted playback support. Counts beyond the authored/tested 3–6 family are not advertised as supported designs.

## Development and publication boundary

The daily-artifact principle governs tangible development progress, not an obligation to post before the artist is ready. These fixtures are engineering proofs, not artist-approved designs or public releases. Exported artwork contains no settings/proof chrome. Any future preview must remain media-first with controls revealed on interaction.

No merge, deployment, social post, private-media publication or public sharing link was authorized or performed in this tranche. No new coding agent was dispatched. An existing failed Copilot run was observed; issue comments and prepared specifications were not treated as dispatch receipts. Execution used the active remote environment without requiring the artist's Mac.

## Remaining gates and next increment

Issue #8 stays open. The engine/render proof does not close earlier-selector identity, TripTicks equivalence, Floating Points raw structural/asset recovery, Up the Hill Backwards visual verification, Narcissus identity or live-browser continuity gates.

The next historical blocking gate is byte retrieval of one already-located source, followed by read-only signature/hash/structure or representative-frame inspection. A resolved Dropbox locator or extracted text alone does not close it. Preserve the eight-render regression family while addressing that bounded gate; do not restart repository discovery or add another framework.

Later circles—generative audio, explicit bounded modulation, persistent web, controlled audience interaction, walkable 3D, embodiment and physical installation—remain extension directions, not tasks or completion claims for this tranche. Portvs remains the implementation boundary until a separately authorized promotion decision is supported by an executable need.
