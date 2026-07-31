# Omega substrate bootstrap receipts

These receipts have distinct custody roles:

- `initial-bootstrap-apply-report.json` is historical evidence from the first
  live apply. Its nonempty `applied` list is intentionally bound to the earlier
  manifest digest recorded in that file.
- `live-bootstrap-report.json` is the current manifest's read-only plan.
- `live-bootstrap-apply-report.json` is the current manifest's apply observation.
  Regenerate it only after a fresh plan proves that `actions` is empty, so the
  observation cannot mutate the Workspace.
- `live-bootstrap-verify-report.json` is the current manifest's strict parity
  observation.

The plan, current apply, and verify receipts must share the SHA-256 digest of
`governance/workspace-manifest.yaml`. Repeated generation must be byte-identical.
