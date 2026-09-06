# Artifact 001 — paired-layout family receipt

Status: **implementation tranche in progress; renders not yet established**.

This receipt records only evidence produced on `work/n-loop-paired-compositions-2026-09-05`. It must not be read as evidence of a render, live-browser playback, historical reconstruction, or artist approval.

## Reconciled starting state

- `main`: `48da3da293ecd7604b6c9d3ce19d0bf49a70013d` at branch creation.
- PR #7 remained open/draft on `work/visual-form-evolutionary-audit-2026-09-05` at `95842ae8f45a4b00f630ad12054c845aa67f30c0`.
- Issue #8 already contained the September 5 N-loop / portrait-landscape amendment.
- No separate open implementation PR matching this scope was found before branch creation.
- Existing renderer remains `render_triptych.py`; this tranche does not replace it.

## Added model evidence

`composition_model.py` separates independent loop/content/time state from presentation layouts. It defines deterministic per-loop source selection, local media clocks, serialization, and model semantics for `hold`, `release`, `reroll`, `swap`, and `move`.

`artifact001_layouts.py` contains explicit engineering layout pairs for N=3,4,5,6. They are authored fixture geometry rather than a generic grid generator. These layouts are **synthetic engineering demonstrations and not artist-approved visual designs**.

`test_composition_model.py` specifies checks for:

- one-to-one active-loop/layout mapping for all eight matrix cells;
- portrait/landscape selection without temporal mutation;
- adding loop 6 without resetting loops 1–5;
- serialization round-trip;
- seeded selection independent of evaluation order;
- local hold/release behavior;
- targeted reroll;
- source-only swap semantics retaining loop clocks;
- orientation-local move semantics;
- explicit rejection of unsupported N=7 until a paired design exists.

## Evidence still required

The GitHub contents API can author and inspect repository code but does not execute Python/ffmpeg. Therefore this branch alone does **not** establish:

1. current Triptych baseline execution;
2. passing unit tests;
3. eight moving renders or reference stills;
4. visual inspection of those renders;
5. media hashes/facts;
6. live-browser orientation continuity;
7. measured simultaneous-playback resource limits;
8. historical compatibility with Floating Points, Up the Hill Backwards, First Circle, TripTicks, or Narcissus.

The next execution environment must run the narrow tests and baseline renderer before any passing/executed claim is promoted.

## Proposed narrow commands (not yet execution evidence)

```bash
cd incubator/triptych-video-canon
python3 -m unittest -v test_composition_model.py
python3 render_triptych.py samples --dry-run
```

Do not check issue #8 execution boxes from this receipt until their actual predicates have been observed.
