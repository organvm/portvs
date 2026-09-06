# NARCISSUS — instrument study 001

Status: reversible incubator experiment, not an approved artwork or release.
Coordination: issue #8; stacked above the unmerged PR #9 implementation. The
historical NARCISSUS work is distinct from this new instrument and from the wider
persona practice. Public code uses synthetic fixtures by default. No original
photograph, archive video, manuscript, recording, or participant file is included.

## Implemented object

A three-role audiovisual instrument with independent SELF, REFLECTION and ECHO
video identities; explicit transformed/nested returns; participant controls;
optional local source and live-input paths; and versioned, forkable recipes.

`build_study.py` imports the existing `composition.py` resolver and
`browser_runtime.py` compiler. The generated HTML embeds the exact pinned
`browser_runtime.js`; it does not copy its selection semantics into a new engine.
The additive adapter calls its existing activation/layout/tick functions. This is
a pinned experiment, not a promise of a stable upstream API. The builder rejects
changed dependency blobs until the adapter is revalidated.

The normalized renderer and browser-plan audio fields remain silent. New sound
and canvas composition live only in this extension. No legacy exporter changes.
The fixed relation graph is validated for known roles, bounded gains and no
zero-delay cycle. The UI is not yet an arbitrary graph editor or N-role runtime.

## First reversible artifact

The builder emits an embedded HTML study, normalized state, compiled plan,
content-addressed clips and custody metadata into ignored `runtime-proof/`.
The synthetic default is safe to use for engineering review. The explicit
`--image` option creates new crop/zoom derivatives of a local JPEG/PNG and verifies
that its original bytes remain unchanged. Such motion is not recovered footage,
reconstructed performance, or historical camera timing. Keep that output private.

The primary layouts are paired landscape and portrait compositions. Three native
video nodes keep their independent clocks through responsive layout changes.
Nested returns and the optional OTHER inset are derived views, not extra loops.
Increasing independent loop count requires a separately authored extension.

## Interaction and persistence

Start/Pause/Resume and Rewind control a bounded sixty-second transport. Sound is
opt-in. SELF/REFLECTION/ECHO buttons or a view click select attention explicitly;
there is no eye tracking. Delay, return gain, degradation, nesting, impulse,
block and freeze alter the relation layer without seeking/remounting the videos.
Reduced-motion mode keeps a static visual baseline.

Save variation downloads a JSON recipe. Open variation checks its checksum,
version, source-state binding, parameter ranges and event order before applying
it. Fork saves the parent recipe ID. Text and source/page notes are retained as
entered; no manuscript excerpts are preselected, paraphrased or voiced.

A recipe preserves parameters, control events, playhead, exact text and ancestry.
It does NOT preserve decoded video buffers, audio oscillator phase, delay-line
contents, participant media bytes, camera pixels or physical microphone input.
Reopening refills image memory. External files require matching SHA-256 relinking.
It is a reproducible control recipe, not a sample/pixel-exact session checkpoint.
There is no public gallery, account backend, multiplayer session or hosting.

Local images/videos appear in an OTHER inset; local audio replaces test tones.
Input files are limited to 20 MiB; decoded visual sources to 20 megapixels and
video/audio duration to ninety seconds. These guards are not hardware guarantees.
Optional camera preview disables excerpt recording and is excluded from the
return buffer. Microphone input contributes only numeric level events; raw
microphone audio is neither monitored nor recorded. Stop, page hide and recipe
load end capture; late permission completion is cancelled. Real device permission
and lifecycle behavior still require device tests; automated providers are fake.

The visual memory is bounded to 26 low-resolution frames (5,990,400 pixel bytes,
excluding other working surfaces). Sound uses loop-phase-modulated engineering
oscillators or a local audio source through a bounded dry/delay/feedback bus.
Feedback is capped at 0.6. The prototype's tones are not the artist's score.
Canvas MediaRecorder exports a local excerpt of at most sixteen seconds;
container/codec support is feature-detected, not promised across browsers.

## Reproduce without archive access

Requires Python 3.10+, FFmpeg/ffprobe with H.264 encoding, Node for pure tests,
and Playwright/Pillow plus an installed browser for native tests. The recorded
run used Python 3.13.5, Node 22.16.0, FFmpeg 7.1.5, Playwright 1.57.0,
Pillow 12.3.0 and installed Chromium 144.0.7559.96. No runtime npm dependency.

From `incubator/triptych-video-canon/`:

```bash
python narcissus/build_study.py --output runtime-proof/narcissus-synthetic-v1
node --test narcissus/test_relations.cjs
python narcissus/test_study.py --study runtime-proof/narcissus-synthetic-v1 \
  --output runtime-proof/narcissus-evidence --browser /usr/bin/chromium
```

Use a fresh output directory; the builder refuses replacement of an existing
study. Browser tests inject the exact generated HTML into an isolated document.
They do not navigate a served site or certify file-open behavior. No browser
policy, CSP or permissions should be disabled to convert a blocked gate to a pass.

Files: `relations.js` (state/validation/audio bus), `instrument.js` (adapter and
interaction), `index.template.html` (technical review UI), `build_study.py`
(builder/custody), `test_relations.cjs` and `test_study.py` (proof),
`EVIDENCE.json` and `EXECUTION.md` (recorded results).

## Control seam and next gates

`narcissusStudy.control({address, value})`, also exposed through the local
`narcissus-control` CustomEvent, accepts:

- `narcissus/echo/delay`, `narcissus/echo/feedback`;
- `narcissus/view/fracture`, `narcissus/view/depth`;
- `narcissus/focus`.

All routes use the same parameter validation/event log. This is NOT a working
Ableton, Max, OSC, MIDI or network bridge. An eventual bridge must map external
messages onto these controls without becoming a second clock/source authority.

Next implementation gates: portable rendered-session replay; a genuinely
editable relation graph; additional independently sourced loop counts with paired
geometry; authored sound/stems and exact text selections; secure served loading;
physical iOS/Safari and other device tests; external performance bridge; and an
explicitly authorized sharing/publication policy. None is closed by a screenshot.

Candidate homes remain Portvs incubation, a separately selected art/runtime
repository, Media Ark for source custody, or an approved new repository. Portfolio
is only a future verified public projection. Promotion requires an owner decision,
artist review of the geometry/sound/interaction, source/participant permissions,
and served/device proofs. No merge, deployment, release or owner promotion is
part of this study.
