# Visual-Form Evolutionary Audit — 2026-09-05

Status: active synthesis
Owner: Portvs incubator while implementation owner remains unresolved
Scope: existing visual/audiovisual works → reusable formal grammar → daily artifact evolution

## Purpose

This audit does not invent a new generative-art project. It identifies an already-emerging lineage across prior works, extracts reusable formal and computational primitives, and defines a production rule: each system increment must remain capable of producing a finished public artifact the same day.

The governing development model is concentric rather than replacement-based. Earlier forms remain valid render targets while later circles add dimensions: still image → moving image → generative timing → generative sound → modulation → persistent web state → audience interaction → spatial world → embodiment → physical installation.

## Evidence posture

Use three confidence states:

- `verified`: implementation or tracked source evidence inspected in the current remote canon.
- `documented`: tracked records name the work or behavior, but the originating implementation/media is not currently available in the remote canon inspected here.
- `user-attested`: supplied directly by the artist in the 2026-09-05 working session; do not silently promote to implementation evidence.

Do not allow conceptual continuity to become implementation evidence.

## Current lineage matrix

| Work / branch | Evidence state | Already established | Reusable primitive | Immediate next evolution |
| --- | --- | --- | --- | --- |
| Triptych / tri-panel selector | documented + user-attested | Three simultaneous image apertures; selection/chance; prior rendered Triptych media exists | `panel topology`, `media-bank selection`, `hold/swap`, `three-part simultaneity` | Recover executable selector if available; normalize as a 3-panel configuration rather than rewrite history |
| Up the Hill Backwards | user-attested | Quad-panel form | `four-panel topology`, multi-view juxtaposition | Locate source/implementation under actual repository or media name; extract topology without presuming behavior not yet verified |
| Narcissus | documented + user-attested | Existing visual/audiovisual branch repeatedly referenced in prior Triptych excavation | Unknown until source inspection | Locate canonical implementation/media before defining its formal contribution |
| Floating Points | documented + user-attested | Dense many-layer moving-image composition; prior render-loss/failure references exist; artist reports ~50–100 Premiere layers with effects | `high-density simultaneity`, `independent temporal layers`, `nested compositing`, `failure boundary of timeline editing` | Treat as formal ancestor of a realtime/generative layer system; do not claim original implementation survives until located |
| iPhone photo-widget compositions | user-attested + current visual evidence | Stable screen topology with independently changing photo banks; chance daily conjunctions | `independent clocks`, `ambient persistence`, `chance pairing`, `background + apertures` | Reproduce as a lightweight configurable runtime with reproducible seeds/holds |
| The Thing Without a Name / Danse Macabre | verified | 2017 still-photo corpus reactivated as deterministic generative WebGL room; pure `f(seed,t)` engine; spatial panel concept; user interaction and physical-room trajectory documented | `deterministic state`, `projective texturing`, `spatial planes`, `independent metamorphosis`, `addressable permalink`, `engine-as-work / render-target model` | Use as the most advanced proven ancestor and compatibility target for the common composition model |
| Visualizer / generative abstract runtime | verified at repository-canon level | Browser-native p5/canvas/WebGL visualizer branches already exist | `parameterized browser runtime`, `generative field`, `web-native interaction` | Reuse or promote only after explicit implementation-owner decision |
| Web / 3D chambers | verified at repository-canon level | Existing WebGL/Three.js room/chamber branch exists in the Visual Form Canon | `navigable spatial runtime` | Use as prior art when the system reaches walkable-space circle |
| Exhibit / kiosk / gallery branch | verified at canon level | Existing promotion aperture for digital frame, kiosk, gallery loop, installation and living-loop contracts | `physical playback target`, `installation contract` | Preserve as downstream render target; do not prematurely build installation infrastructure |

## Verified Danse contribution

`organvm/the-thing-without-a-name` materially changes the baseline. Its preserved generative-engine plan states that the 2017 still-photo work was to become a constantly changing space using screens at different angles/depths/transparencies, with a digital proof preceding physical realization. The plan explicitly defines five faces of one engine: film, living web page, social presence, visitor insertion, and a costed physical-room pitch.

The engine decision `f(seed,t)` is especially important. It provides deterministic reconstruction, O(1) seek, permalinks, synchronized projection potential, and a clean separation between generative state and render target. This should be treated as a direct ancestor of the new composition core, not an isolated one-off implementation.

The current canonical repository also preserves project lineage in `LINEAGE.json`, including the migration from `organvm/limen/apps/danse` and verification invariants.

## Existing Visual Form Canon findings that already support this synthesis

The Portvs Visual Form Canon has already established the broader object as:

```text
source set + visual grammar + runtime target + remix transforms + public/private boundary + promotion target
```

Its current remote census found 48 visual-form candidate repositories and explicitly identifies reusable branches for:

- Triptych / time-based media
- ambient screensaver / wallpaper runtime
- visualizer / generative abstract runtime
- web / 3D chambers
- Media Ark source custody
- portfolio / public gateway
- exhibit / kiosk / gallery
- lifecycle / generated-form governance

Therefore this audit extends an existing unification effort rather than creating a competing canon.

## Normalized composition model — first draft

The common model should be application-independent enough that an old work can be described without pretending it was originally built in the future engine.

```text
Composition
  id
  lineage[]
  source_sets[]
  topology
  layers[]
  global_state
  timing
  routing[]
  seed
  render_target

Layer
  id
  source_ref
  media_type
  x / y / z
  width / height
  rotation
  opacity
  blend
  playback_state
  selection_strategy
  local_clock
  transforms[]
  modulation_inputs[]

Routing
  source_parameter
  transform
  destination_parameter
  amount
  polarity
  curve
  smoothing
  probability
  condition
```

This is deliberately broader than `Panel`: a later layer may be a light, sound emitter, particle field, mesh, text surface, camera, or physical output.

## Historical preservation rule

Do not rewrite original works to make them look natively authored in the normalized engine.

Use:

```text
original artifact
    ↓ preserve
formal analysis
    ↓
compatibility description
    ↓
new-system reimplementation / descendant
```

Every descendant must retain explicit provenance back to its source work.

## Concentric circles — revised from existing state

### Circle A — archaeology and normalization

Objective: locate surviving code/media/records for Triptych, Up the Hill Backwards, Narcissus, Floating Points, Danse, and adjacent visual-form ancestors.

Deliverable per recovered work:

- source location
- evidence state
- original runtime/tool
- media corpus
- topology
- timing model
- chance/randomness
- compositing model
- interaction
- audio behavior
- spatial behavior
- reproducibility
- export/render targets
- unique primitive contributed to the canon

### Circle B — common 2D visual engine

Objective: consume recovered primitives as configurations rather than hard-coded separate apps.

Required initial modes:

- triptych
- quad
- ambient widget-like composition
- arbitrary N-layer composition

Required controls:

- hold
- reroll
- swap
- move
- seed
- capture

### Circle C — generative audio

Audio must be a first-class generative process, not a soundtrack file. Add independent musical state capable of producing a different valid realization per seed/time/state.

Minimum parameter families:

- tempo/timebase
- density
- pitch/tuning field
- rhythm probability
- sample/source bank
- synthesis parameters
- spatialization
- effect state

### Circle D — modulation matrix

Everything need not affect everything at once; everything should be potentially routable through explicit bounded mappings.

Primitive:

```text
source → transform → destination
```

Mappings may be direct, conditional, probabilistic, feedback-bounded, or disabled. Modulation depth itself may be modulated.

### Circle E — persistent public runtime

Website evolves from archive to live renderer. Preserve both:

- artifact: captured occurrence
- world: process capable of producing occurrences

### Circle F — audience interaction

Visitors receive bounded parameters or compositional gestures, not unrestricted access to the private authoring/runtime system.

### Circle G — walkable 3D world

Extrude the existing panel/spatial grammar into navigable space. The first 3D world should be a spatial descendant of prior work, not a generic game environment.

### Circle H — embodiment / mocap

Body joints, velocity, orientation and gesture become modulation sources. Mocap enters only after the world is independently compelling.

### Circle I — physical installation

Projectors, displays, lights, sensors and spatial sound become physical render targets of the same composition state.

## Daily-artifact invariant

No development streak should exceed one day without a visible and/or audible artifact.

Each workday records:

```text
system version
source lineage
new capability
seed/state
artifact path/url
publication surfaces
observed failure or discovery
next mutation
```

Engineering work that cannot be demonstrated in that day's artifact should be deprioritized unless it is a blocking repair.

## Initial daily artifact sequence

This is a starting queue; substitute a more evidentially grounded ancestor whenever source recovery changes the order.

| Day | System move | Artifact |
| --- | --- | --- |
| 001 | Recover/present Triptych ancestor | Existing or reconstructed three-panel composition with provenance |
| 002 | Add reproducible media selection | Seeded triptych state; compare two seeds |
| 003 | Add independent panel clocks | Short moving triptych showing asynchronous change |
| 004 | Recover quad topology from Up the Hill Backwards | Four-panel state; no invented behavior beyond verified source |
| 005 | Make topology configurable 3 ↔ 4 | One artifact demonstrating both as sibling configurations |
| 006 | Recover one verified Narcissus primitive | Artifact isolates that primitive inside common engine |
| 007 | Reintroduce Floating Points density principle | Higher-density composition with bounded active-source count |
| 008 | Add nested compositing | One panel contains its own multi-source composite |
| 009 | Add z-depth / parallax | First shallow spatialization without full walkable 3D |
| 010 | Add first generative audio voice | Same visual state rendered with deterministic generative sound |
| 011 | Add image → audio mapping | One explicit bounded modulation |
| 012 | Add audio → image mapping | Reverse causal direction |
| 013 | Add modulation amount as a parameter | Demonstrate meta-modulation |
| 014 | Add browser live-state surface | Public page runs current state and can freeze/capture |

The queue should remain flexible. The invariant is one artifact per day, not blind adherence to a calendar.

## Immediate engineering objective

Do not begin Unreal, Max/MSP/Jitter, TouchDesigner, mocap, or installation infrastructure yet.

First prove a common composition state in the smallest executable environment already compatible with the existing canon. The initial implementation should:

1. model 3-panel and 4-panel topologies as data;
2. support still/video sources;
3. provide independent local clocks;
4. support seeded selection;
5. implement hold/reroll/swap/move;
6. serialize the complete state needed to recreate an artifact;
7. export a still and a short moving capture path;
8. leave routing/audio fields in the state schema even if they are initially inert.

The first architectural test is not visual sophistication. It is whether one state description can reproduce both a Triptych-descended artifact and a quad-descended artifact without separate hard-coded applications.

## Source-recovery gates still open

### Triptych

Remote records verify that the 2026-07-06 excavation found:

- `TripTicks.mp4`
- `story-triptych.mp4`
- `session-meta/TRIPTYCH.md`
- additional Triptych references in prior session records

Those assets were local-only and were not copied into git. Source recovery remains incomplete until the implementation and/or media is available remotely or the workstation archive is restored.

### Up the Hill Backwards

Literal-title search against the currently accessible remote GitHub canon did not locate a convincing project implementation. Treat the quad-panel behavior as user-attested until the actual source/media is located.

### Narcissus

Narcissus is repeatedly named in the Triptych excavation and audiovisual-account records, but the inspected remote canon has not yet yielded a canonical implementation. Do not define its unique computational grammar until located.

### Floating Points

Remote textual evidence confirms Floating Points as an established project/lineage item and references a prior render-loss/failure state. Current working-session evidence supplies the Premiere multi-layer implementation history. Original project/source recovery remains open.

## Promotion decision

Keep this synthesis in Portvs for now because the object is still lineage + grammar + promotion logic. Do not choose the final implementation owner until the first normalized executable proves which existing runtime branch should absorb it.

Promote only when one of these becomes the next durable object:

- reusable source ingestion/indexing → Media Ark
- public narrative / commerce gateway → portfolio
- concrete browser/3D artistic runtime → art-runtime repository
- physical playback contract → exhibit/art repository

## Next action

1. Continue source recovery for the four unresolved ancestors: Triptych implementation, Up the Hill Backwards, Narcissus, Floating Points.
2. When one executable ancestor is recovered, create the first normalized `Composition` fixture from it.
3. Build the smallest renderer capable of reproducing that fixture.
4. Publish Artifact 001 from that renderer or, if source recovery remains blocked, publish an archival ancestor with explicit provenance while engineering continues.
5. Every subsequent implementation increment must produce or materially improve a public artifact.
