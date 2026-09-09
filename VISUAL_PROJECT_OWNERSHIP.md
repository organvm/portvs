# Visual project ownership — September 9, 2026

Technical coordination record; not artist-authored exhibition copy.

The artist states that PORTVS was intended as a portal to the rest of the project
universe and asks for Narcissus to have its own repository connected to the persona
project, the other visual work, and MET4morfoses. That choice resolves ownership
that earlier incubation records left open.

| Surface | Responsibility | Current state |
| --- | --- | --- |
| PORTVS | Portal, links and coordination history | Existing repository |
| `organvm/narcissus` | Narcissus history, source relationships, work-specific instrument and recipes | Standalone Git repository prepared locally; remote provisioning pending |
| `organvm/visual-composition-engine` | Shared composition/compiler/rendering tooling | Descriptive proposed repository name; standalone Git prepared locally; remote provisioning pending |
| [MET4morfoses](https://github.com/organvm-ii-poiesis/ivi374ivi027-05) | Literary source editions | Existing canonical web-edition repository |
| Persona project | Cross-work identity and project catalogue | Existing work/thread IDs retained; no unrelated persona-named repository assigned |

## Historical relationship

The artist describes taking a selfie at a friend's party in Florida during the
FAU MFA, having another person photograph that act, sending the resulting image
to a friend, and another person photographing the friend looking at the image.
This is artist testimony supplied September 9; exact date, named participants,
original media and capture timing are not inferred from screenshots.

The defining sequence contains capture, transmission, viewing and another capture.
Study 001's three independent SELF/REFLECTION/ECHO sources are a new interpretation,
not the historical sequence itself. PER-W-0005 (historical Narcissus) and PER-W-0010
(study 001) remain distinct catalogue identities. Floating Points, Up the Hill
Backwards, Wrung You and the collage documented under the album label “noonlight”
also remain distinct works.

## Literary connection

The deposited thesis introduction corroborates the MFA application-story-to-thesis
relationship. The [introduction](https://github.com/organvm-ii-poiesis/ivi374ivi027-05/blob/a022f8a411b7dd1c5f24aff9aceee5ee36e716a1/src/content/intro.md)
contains the Narcissus 2014 / @NARSISVS 2018 comparison. The canonical
[cycle-3 text](https://github.com/organvm-ii-poiesis/ivi374ivi027-05/blob/a022f8a411b7dd1c5f24aff9aceee5ee36e716a1/src/content/sikl-3.md)
and [source manifest](https://github.com/organvm-ii-poiesis/ivi374ivi027-05/blob/a022f8a411b7dd1c5f24aff9aceee5ee36e716a1/src/data/canonical-manifest.json)
locate the Narcissus/Echo material. Source editions and original typography must
remain distinct; linking the text does not create new manuscript prose or a score.

## Code extraction and custody

- [PR #9](https://github.com/organvm/portvs/pull/9), inspected head
  `c9fa438847da98cbb6901c032f94ca443f607a21`: extracted the complete
  `incubator/triptych-video-canon/` tooling directory as the shared-engine root.
- [PR #10](https://github.com/organvm/portvs/pull/10), inspected head
  `11d8d361ca6c8fb7758aeeecd09b74d57d21557b`: extracted its ten-file
  `incubator/triptych-video-canon/narcissus/` subtree as the work repository root.
- Isolated Git subdirectory filtering preserves relevant authorship/history and
  source blobs while necessarily producing new commit IDs. Original PORTVS refs
  were not rewritten.
- Narcissus now accepts an explicit external engine directory; the three original
  engine blob pins are unchanged. Output is local to its own `runtime-proof/`.
- Initial engine extraction matched all 77 source file blobs. Its 88-test
  model/compiler/renderer shard passed. Narcissus passed 32 relation/compiler/
  extraction tests and produced a standalone synthetic build. New extraction
  receipts are separate from the September 6 execution history.

## Cutover state

The current GitHub tools can write existing repositories but cannot create a new
repository. The complete standalone sources, Git bundles and verification records
are prepared as the task's downloadable deliverable. Neither destination is
presented as an existing remote repository. No main-branch removal is made while
those destinations are unavailable. PR #9 and #10 remain draft development records.

Once the remote repositories exist, import the verified standalone histories,
verify destination heads and builds, then replace incubator implementations with
stable links through a reviewed cutover. Do not merge PR #10 into PORTVS merely
to overcome the missing destination; do not discard it before verifying custody.

The next Narcissus study should represent explicit image/event relationships and
participant continuation of the capture/viewing sequence. Reuse the existing
controls, media binding and recipe ancestry. An arbitrary witness graph, original
video reconstruction, physical-device proof and hosted publication are not
implemented by moving the code.
