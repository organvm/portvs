# Portvs Agent Protocol

Read this file at session start. Portvs is the reflection membrane and work graph,
not a dumping ground for every new idea.

## Operating Rule

When the human is unsure where something belongs, use an incubator lane. Do not
pretend the final owner is known, and do not scatter files across the repo.

Incubation means:

- Identify the smallest durable decision that is actually known.
- Keep new work inside `incubator/<slug>/`.
- Build the smallest reversible artifact that helps the human keep moving.
- Record candidate promotion homes in the incubator note.
- Move/promote later only after the artifact proves its shape.

## Creative Work

Creative product/device ideas may begin inside Portvs when their final owner is
unclear. In that mode, Portvs is the conductor/incubator, not the permanent
implementation claim.

For each incubated device, create or update `incubator/<slug>/INCUBATION.md`:

- What is the object?
- What is the first reversible artifact?
- What files were created?
- Candidate promotion targets: Portvs, Media Ark, portfolio, a-mavs-olevm,
  a new repo, or archive.
- What evidence would justify promotion?

For the triptych / three-video Instagram Story device, the allowed working path is
`incubator/triptych-video-canon/`. The creative session may build a renderer,
manifest, sample workflow, or export notes there. Do not add repo-root
dependencies or mutate `graph.jsonl` until promotion is chosen.

## Boundaries

- Do not touch Limen from a Portvs worktree.
- Do not use `config/_limen` as a place for new work.
- Do not create broad architecture unless the task is explicitly architecture work.
- Do not treat web search as implementation permission.
- Keep experiments reversible and named by one clear branch or worktree.

## Verification

Before reporting completion, run:

```bash
git status --short --branch --ahead-behind
```

For code changes, also run the narrow relevant test or script. For placement-only
work, a clean or intentionally scoped git status is the predicate.
