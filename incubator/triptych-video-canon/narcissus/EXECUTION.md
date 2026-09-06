# NARCISSUS study 001 — executed proof

Date: September 6, 2026. Upstream: `beecfee905cb2685b7c71ede13a1955faed6c153`.
The three dependency blobs pinned in `build_study.py` were fetched through the
connected repository and match local Git-object hashes exactly. They are unchanged.

## Completed scoped tests

46 distinct tests passed: 18 Node relation/state/checksum tests plus 6 existing-
compiler boundary/integrity tests and 22 native Chromium instrument tests.
Zero failures, errors or skips in the final complete synthetic run. Counts exclude
development reruns. The same 28 Python/browser cases also passed against a
private moving-still build; that replay is not 28 additional unique tests.
Upstream PR #9's ninety-test suite was NOT rerun here and is not added to this count.

The browser used real HTMLVideoElements, decoders, clocks, Canvas, AudioContext,
OfflineAudioContext and MediaRecorder. The transport was explicit isolated-
document HTML injection with embedded bytes and an actual portable SHA-256
computation, not an injected expected digest. Native camera/microphone lifecycle
cases used synthetic providers; no physical-device or granted-permission claim.

The armed responsive-layout test preserved all three native node references and
source URLs with no observed seeks, loads, pauses, rate changes or child mutations.
At approximately 0.9944 seconds elapsed, each native time advanced approximately
0.994453 seconds. This is a short bounded window, not indefinite continuity or
zero dropped-frame proof. Independent source wraps remain compiled boundaries.

Return memory reached its explicit 26-frame / 5,990,400-pixel-byte bound. Tests
also exercised pause/resume, event replay, rewind/new impulse, native controls,
exact text download/import, parent retention, checksum rejection before mutation,
file relinking and wrong-byte rejection, local WAV source replacement, opt-in
nonzero sound, delayed audio, recorded A/V, mobile control fit at 320 CSS pixels,
reduced-motion baseline, late permission cancellation, capture stop, camera
recording exclusion, numeric microphone envelopes and control-address validation.

## Audio and capture limits exposed by measurement

A real 48 kHz OfflineAudioContext impulse test produced amplitudes approximately
0.14, 0.09, 0.036 and 0.0144 at samples 0, 12000, 24128 and 36256 respectively.
Blocking return left only the direct impulse. The first return matches 0.25 s;
later cyclic traversals acquired 128 additional samples each in this Chromium.
The test records actual onsets and gain decay; no sample-exact cyclic-delay claim.
The live graph analyser and decoded excerpt audio were nonzero.

The native synthetic excerpt decoded as VP8 video and Opus audio. A separate
private study capture was also decoded and converted to a 9.3-second H.264/AAC
MP4 for review. It is an actual interactive-runtime capture with provisional
procedural sound, not an authored score or recovered historical moving image.
Private media/captures and their private-source bindings are not committed here.

## Failures and unclosed gates

The default Playwright browser executable was absent; an installed Chromium was
used explicitly. Direct file navigation failed with `ERR_BLOCKED_BY_ADMINISTRATOR`.
No browser policy was changed. Served HTTP/WebCrypto loading is not proven by
this embedded adapter and remains open, as in upstream PR #9.

An initial development test run wrongly assumed sample-exact feedback cycles,
split a data URL at a comma inside its codec MIME parameter, and reinjected a
script with top-level lexical bindings into the same document. The final harness
measures actual feedback onsets, extracts the final base64 segment, and tests
reduced-motion in a fresh document. One private rerun was interrupted by the tool
time limit; the final complete private run passed. Failed/interrupted runs are
not reclassified as passes. Original failure logs are retained in the delivery kit.

`git status --short --branch --ahead-behind` on the scoped local source snapshot
returned `fatal: not a git repository`. It is not a full checkout or a claim of
whole-repository cleanliness. Repository writes must be checked separately by
remote tree/commit/PR comparison, with only incubator changes and no force update.
No hosted CI success or human review has been inferred from local tests.

Historical moving-media recovery, full-screen source-specific geometry, approved
sound/text, pixel/audio checkpoint replay, arbitrary graph editing, higher role
counts, physical devices, Ableton/Max integration, source permissions and an
approved public release remain separate gates. Keep this study and PR #9 draft.
