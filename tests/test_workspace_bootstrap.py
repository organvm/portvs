from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
JACK = ROOT / "jack.sh"
BOOTSTRAP = ROOT / "runtime" / "workspace_bootstrap.py"
REQUIREMENTS = ROOT / "requirements.txt"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            *args,
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def _manifest(
    tmp_path: Path, *, include_legacy: bool = False
) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "Scratch" / "Workspace"
    remote = tmp_path / "remote.git"
    remote.mkdir()
    _git(remote, "init", "--bare", "-q")
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-q")
    (seed / "README.md").write_text("seed\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-qm", "seed")
    _git(seed, "branch", "-M", "main")
    _git(seed, "remote", "add", "origin", str(remote))
    _git(seed, "push", "origin", "main")
    data = {
        "schema": "portvs.workspace_manifest.v1",
        "workspace_root": str(workspace),
        "limits": {
            "max_scan_entries": 1000,
            "max_violations": 0,
            "max_unmeasured": 0,
            "max_compatibility_links": 0,
        },
        "rows": [
            {
                "path": "library",
                "kind": "structural",
                "owner_ref": "portvs",
                "residency": "structural",
            },
            {
                "path": "library/engine",
                "kind": "structural",
                "owner_ref": "portvs",
                "residency": "structural",
            },
            {
                "path": "library/engine/organvm",
                "kind": "structural",
                "owner_ref": "portvs",
                "residency": "structural",
            },
            {
                "path": "library/engine/organvm/tool",
                "kind": "repository",
                "owner_ref": "organvm/tool",
                "residency": "laptop",
                "remote": str(remote),
                "custody_ref": "refs/remotes/origin/main",
                "default_branch": "main",
                "legacy_paths": ["tool-old"] if include_legacy else [],
            },
            {
                "path": "library/underworld",
                "kind": "structural",
                "owner_ref": "portvs",
                "residency": "structural",
            },
            {
                "path": "library/underworld/archive-index.json",
                "kind": "index",
                "owner_ref": "portvs",
                "residency": "remote-index",
                "source_ref": "https://example.invalid/archives",
                "generator": "jack.sh --refresh-index",
            },
            {
                "path": "runtime",
                "kind": "structural",
                "owner_ref": "limen",
                "residency": "structural",
            },
            {
                "path": "runtime/worktrees",
                "kind": "ephemeral",
                "owner_ref": "limen",
                "residency": "ephemeral",
                "expires_after": 3600,
                "reaper": "limen reap",
            },
        ],
        "migration": {"compatibility_links": []},
    }
    manifest = tmp_path / "workspace-manifest.yaml"
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return manifest, workspace, remote


def _run(
    manifest: Path, workspace: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(JACK),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            *args,
        ],
        capture_output=True,
        text=True,
    )


def _load(manifest: Path) -> dict[str, object]:
    return yaml.safe_load(manifest.read_text(encoding="utf-8"))


def _write(manifest: Path, data: dict[str, object]) -> None:
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_plan_is_read_only_and_json_bounded(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    proc = _run(manifest, workspace, "--plan", "--json")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["mode"] == "plan"
    assert report["actions"]
    assert not workspace.exists()


def test_reconstructs_empty_scratch_root_and_second_run_is_idempotent(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    first = _run(manifest, workspace, "--json")
    assert first.returncode == 0, first.stdout + first.stderr
    first_report = json.loads(first.stdout)
    assert first_report["applied"]
    second = _run(manifest, workspace, "--json")
    assert second.returncode == 0, second.stdout + second.stderr
    second_report = json.loads(second.stdout)
    assert second_report["applied"] == []
    assert second_report["actions"] == []
    assert second_report["blockers"] == []
    assert (workspace / "runtime" / "worktrees").is_dir()
    assert (workspace / "library" / "engine" / "organvm" / "tool" / ".git").exists()
    assert (workspace / "library" / "underworld" / "archive-index.json").is_file()


def test_verify_rejects_undeclared_root_and_missing_empty_container(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    assert _run(manifest, workspace).returncode == 0
    (workspace / "surprise").mkdir()
    (workspace / "runtime" / "worktrees").rmdir()
    proc = _run(manifest, workspace, "--verify", "--json")
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    paths = {row["path"] for row in report["failures"]}
    assert {"surprise", "runtime/worktrees"} <= paths


def test_legacy_repository_blocks_duplicate_hydration(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path, include_legacy=True)
    legacy = workspace / "tool-old"
    legacy.mkdir(parents=True)
    proc = _run(manifest, workspace, "--json")
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert any(
        row["path"] == "library/engine/organvm/tool"
        and "legacy source present" in row["detail"]
        for row in report["blockers"]
    )
    assert not (workspace / "library" / "engine" / "organvm" / "tool").exists()


def test_traversal_and_symlink_escape_fail_closed(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data["rows"].append(
        {
            "path": "../escape",
            "kind": "structural",
            "owner_ref": "x",
            "residency": "structural",
        }
    )
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    proc = _run(manifest, workspace, "--plan", "--json")
    assert proc.returncode == 1
    assert "unsafe relative path" in json.loads(proc.stdout)["error"]


def test_plan_can_write_bounded_receipt(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    receipt = tmp_path / "receipts" / "plan.json"
    proc = _run(manifest, workspace, "--plan", "--json", "--receipt", str(receipt))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(receipt.read_text(encoding="utf-8"))["mode"] == "plan"


def test_runtime_dependency_is_locked_and_missing_dependency_is_structured(
    tmp_path: Path,
) -> None:
    lock = REQUIREMENTS.read_text(encoding="utf-8")
    assert "PyYAML==6.0.3" in lock
    assert "--hash=sha256:" in lock
    manifest, workspace, _ = _manifest(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            "-S",
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--plan",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "requirements.txt" in report["error"]
    assert "Traceback" not in proc.stderr


def test_repository_requires_declared_custody_ref_to_exist(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    assert _run(manifest, workspace).returncode == 0
    repo = workspace / "library" / "engine" / "organvm" / "tool"
    _git(repo, "update-ref", "-d", "refs/remotes/origin/main")

    planned = _run(manifest, workspace, "--plan", "--json")
    assert any(
        row["path"] == "library/engine/organvm/tool"
        and "declared repository" in row["detail"]
        for row in json.loads(planned.stdout)["blockers"]
    )
    verified = _run(manifest, workspace, "--verify", "--json")
    assert any(
        row["path"] == "library/engine/organvm/tool" and "custody_ref" in row["detail"]
        for row in json.loads(verified.stdout)["failures"]
    )


def test_expired_compatibility_link_is_never_planned(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["migration"]["compatibility_links"] = [
        {
            "path": "runtime-old",
            "target": "runtime/worktrees",
            "owner_ref": "limen",
            "expires_at": "2000-01-01T00:00:00Z",
        }
    ]
    _write(manifest, data)

    proc = _run(manifest, workspace, "--plan", "--json")
    assert proc.returncode == 0
    report = json.loads(proc.stdout)
    assert not any(row["operation"] == "symlink" for row in report["actions"])
    assert any(
        row["path"] == "runtime-old" and "expired" in row["detail"]
        for row in report["blockers"]
    )


def test_verify_stops_at_declared_scan_limit(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    assert _run(manifest, workspace).returncode == 0
    data = _load(manifest)
    data["limits"]["max_scan_entries"] = 3
    _write(manifest, data)
    for index in range(20):
        (workspace / f"undeclared-{index:02d}").mkdir()

    proc = _run(manifest, workspace, "--verify", "--json")
    assert proc.returncode == 1
    failures = json.loads(proc.stdout)["failures"]
    assert sum(row["operation"] == "verify-unmeasured" for row in failures) == 1
    assert sum(row["detail"] == "undeclared structural entry" for row in failures) <= 3


@pytest.mark.parametrize(
    ("row_path", "field", "replacement_kind"),
    [
        ("library/engine/organvm/tool", "remote", None),
        ("library/engine/organvm/tool", "custody_ref", None),
        ("library/underworld/archive-index.json", "source_ref", None),
        ("runtime/worktrees", "reaper", None),
        ("runtime/worktrees", "custody_label", "private"),
    ],
)
def test_kind_specific_fields_fail_as_structured_contract_errors(
    tmp_path: Path,
    row_path: str,
    field: str,
    replacement_kind: str | None,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    row = next(row for row in data["rows"] if row["path"] == row_path)
    if replacement_kind:
        row["kind"] = replacement_kind
    row.pop(field, None)
    _write(manifest, data)

    proc = _run(manifest, workspace, "--plan", "--json")
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert report["mode"] == "plan"
    assert field in report["error"]
    assert "Traceback" not in proc.stderr


def test_private_containers_are_created_and_repaired_to_mode_0700(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["rows"].extend(
        [
            {
                "path": "private",
                "kind": "structural",
                "owner_ref": "private-inventory",
                "residency": "structural",
            },
            {
                "path": "private/life",
                "kind": "private",
                "owner_ref": "private-inventory/life",
                "residency": "private",
                "custody_label": "workspace-private-life",
                "sealed_inventory_ref": "receipt://sealed",
                "restoration_receipt_ref": "receipt://restored",
            },
        ]
    )
    _write(manifest, data)
    assert _run(manifest, workspace).returncode == 0
    private = workspace / "private" / "life"
    assert stat.S_IMODE(private.stat().st_mode) == 0o700

    os.chmod(private, 0o755)
    verified = _run(manifest, workspace, "--verify", "--json")
    assert any(
        row["path"] == "private/life" and "0700" in row["detail"]
        for row in json.loads(verified.stdout)["failures"]
    )
    planned = _run(manifest, workspace, "--plan", "--json")
    assert any(
        row["operation"] == "chmod-private" and row["path"] == "private/life"
        for row in json.loads(planned.stdout)["actions"]
    )
    assert _run(manifest, workspace).returncode == 0
    assert stat.S_IMODE(private.stat().st_mode) == 0o700


def test_compatibility_target_must_be_safe_and_canonically_valid(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["migration"]["compatibility_links"] = [
        {
            "path": "runtime-old",
            "target": "runtime/worktrees",
            "owner_ref": "limen",
            "expires_at": "2999-01-01T00:00:00Z",
        }
    ]
    _write(manifest, data)
    outside = tmp_path / "outside"
    outside.mkdir()
    workspace.mkdir(parents=True)
    (workspace / "runtime").mkdir()
    (workspace / "runtime" / "worktrees").symlink_to(outside, target_is_directory=True)

    proc = _run(manifest, workspace, "--plan", "--json")
    report = json.loads(proc.stdout)
    assert not any(row["operation"] == "symlink" for row in report["actions"])
    assert any(
        row["path"] == "runtime-old"
        and "symlink component escapes Workspace" in row["detail"]
        for row in report["blockers"]
    )
    assert not (workspace / "runtime-old").exists()


def test_blocked_parent_suppresses_descendant_actions(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    workspace.mkdir(parents=True)
    (workspace / "library").write_text("occupied\n", encoding="utf-8")

    proc = _run(manifest, workspace, "--json")
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "error" not in report
    assert any(
        row["path"] == "library/engine" and "ancestor is blocked" in row["detail"]
        for row in report["blockers"]
    )
    assert not (workspace / "library" / "engine").exists()
    assert (workspace / "runtime" / "worktrees").is_dir()


def test_verify_never_traverses_an_escaping_symlink(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "outside-secret").mkdir()
    workspace.mkdir(parents=True)
    (workspace / "library").symlink_to(outside, target_is_directory=True)

    proc = _run(manifest, workspace, "--verify", "--json")
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    rendered = json.dumps(report)
    assert "symlink component escapes Workspace" in rendered
    assert "outside-secret" not in rendered


def test_plan_never_traverses_a_workspace_root_symlink(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    outside = tmp_path / "outside-root"
    outside.mkdir()
    (outside / "outside-secret").mkdir()
    workspace.parent.mkdir(parents=True)
    workspace.symlink_to(outside, target_is_directory=True)

    proc = _run(manifest, workspace, "--plan", "--json")
    report = json.loads(proc.stdout)
    assert report["actions"] == []
    assert report["blockers"] == [
        {
            "detail": "Workspace root must be a physical directory",
            "operation": "blocked",
            "path": ".",
        }
    ]
    assert "outside-secret" not in json.dumps(report)


def test_failure_receipt_preserves_partial_apply_actions(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    repo = next(
        row for row in data["rows"] if row["path"] == "library/engine/organvm/tool"
    )
    repo["remote"] = str(tmp_path / "missing-remote.git")
    _write(manifest, data)
    receipt = tmp_path / "receipts" / "failed-apply.json"

    proc = _run(manifest, workspace, "--json", "--receipt", str(receipt))
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert report["mode"] == "apply"
    assert report["applied"]
    assert report["failed_action"]["operation"] == "clone"
    assert stored["applied"] == report["applied"]
    assert stored["failed_action"] == report["failed_action"]
    assert stored["workspace_root"] == "$WORKSPACE_ROOT"
