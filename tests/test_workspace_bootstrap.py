from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest
import yaml

from runtime import workspace_bootstrap


ROOT = Path(__file__).resolve().parents[1]
JACK = ROOT / "jack.sh"
BOOTSTRAP = ROOT / "runtime" / "workspace_bootstrap.py"
MANIFEST = ROOT / "governance" / "workspace-manifest.yaml"
REQUIREMENTS = ROOT / "requirements.txt"
RECEIPT_DIR = ROOT / "docs" / "continuations" / "omega-substrate-literal"
HISTORICAL_APPLY_RECEIPT = RECEIPT_DIR / "initial-bootstrap-apply-report.json"
LIVE_APPLY_RECEIPT = RECEIPT_DIR / "live-bootstrap-apply-report.json"
LIVE_PLAN_RECEIPT = RECEIPT_DIR / "live-bootstrap-report.json"
LIVE_VERIFY_RECEIPT = RECEIPT_DIR / "live-bootstrap-verify-report.json"


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


def _compatibility_link(
    path: str,
    target: str = "runtime/worktrees",
    expires_at: str = "2999-01-01T00:00:00Z",
) -> dict[str, str]:
    return {
        "path": path,
        "target": target,
        "owner_ref": "limen",
        "expires_at": expires_at,
    }


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


@pytest.mark.parametrize(
    "surface",
    [
        "row",
        "compatibility_path",
        "compatibility_target",
    ],
)
def test_trailing_slashes_are_structured_contract_errors_without_mutation(
    tmp_path: Path,
    surface: str,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    if surface == "row":
        data["rows"][0]["path"] = "library/"
    else:
        link = _compatibility_link("runtime-old")
        field = "path" if surface == "compatibility_path" else "target"
        link[field] += "/"
        data["migration"]["compatibility_links"] = [link]
    _write(manifest, data)
    receipt = tmp_path / "receipts" / f"{surface}.json"

    proc = _run(manifest, workspace, "--json", "--receipt", str(receipt))

    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "non-normalized relative path" in report["error"]
    assert json.loads(receipt.read_text(encoding="utf-8")) == report
    assert "Traceback" not in proc.stderr
    assert not workspace.exists()


def test_row_index_defensively_validates_paths() -> None:
    with pytest.raises(
        workspace_bootstrap.ContractError,
        match="non-normalized relative path",
    ):
        workspace_bootstrap._row_by_path({"rows": [{"path": "library/"}]})


def test_plan_can_write_bounded_receipt(tmp_path: Path) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    receipt = tmp_path / "receipts" / "plan.json"
    proc = _run(manifest, workspace, "--plan", "--json", "--receipt", str(receipt))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(receipt.read_text(encoding="utf-8"))["mode"] == "plan"


def test_receipt_transform_is_recursive_deterministic_and_idempotent(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "Workspace"
    report = {
        "schema": "test",
        "mode": "verify",
        "ok": False,
        "workspace_root": str(workspace),
        "failures": [
            {
                "operation": "verify-fail",
                "path": "zeta/child-b",
                "detail": "undeclared structural entry",
            },
            {
                "operation": "verify-fail",
                "path": "child-c",
                "detail": "undeclared structural entry",
            },
            {
                "operation": "verify-fail",
                "path": "zeta/child-a",
                "detail": "undeclared structural entry",
            },
            {
                "operation": "verify-fail",
                "path": "runtime",
                "detail": f"failed at {workspace}/runtime",
            },
        ],
        "future": {
            "nested": [
                str(workspace / "private"),
                {"message": f"root {workspace}: unavailable"},
            ]
        },
    }
    original = json.loads(json.dumps(report))

    prepared = workspace_bootstrap._prepare_receipt_report(report, workspace)
    prepared_again = workspace_bootstrap._prepare_receipt_report(
        prepared,
        workspace,
    )

    assert report == original
    assert prepared_again == prepared
    assert prepared["ok"] is False
    assert prepared["failure_count"] == 4
    assert str(workspace) not in json.dumps(prepared)
    aggregates = [
        row
        for row in prepared["failures"]
        if row["detail"] == "undeclared structural entries aggregated"
    ]
    assert [row["path"] for row in aggregates] == [".", "zeta"]
    expected_names = {
        ".": ["child-c"],
        "zeta": ["child-a", "child-b"],
    }
    for row in aggregates:
        names = expected_names[row["path"]]
        digest_input = json.dumps(
            names,
            separators=(",", ":"),
        ).encode("utf-8")
        assert row["count"] == len(names)
        assert row["child_names_sha256"] == hashlib.sha256(digest_input).hexdigest()


def test_verify_receipt_aggregates_names_without_changing_stdout(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    assert _run(manifest, workspace).returncode == 0
    root_names = ["sensitive-alpha", "sensitive-beta"]
    nested_names = ["sensitive-gamma"]
    for name in root_names:
        (workspace / name).mkdir()
    for name in nested_names:
        (workspace / "library" / name).mkdir()
    receipt = tmp_path / "receipts" / "verify.json"

    first = _run(
        manifest,
        workspace,
        "--verify",
        "--json",
        "--receipt",
        str(receipt),
    )

    assert first.returncode == 1
    stdout_report = json.loads(first.stdout)
    stdout_text = json.dumps(stdout_report)
    for name in root_names + nested_names:
        assert name in stdout_text
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    stored_text = json.dumps(stored)
    assert stored["ok"] is False
    assert stored["failure_count"] == len(stdout_report["failures"])
    assert str(workspace) not in stored_text
    for name in root_names + nested_names:
        assert name not in stored_text
    aggregates = [
        row
        for row in stored["failures"]
        if row["detail"] == "undeclared structural entries aggregated"
    ]
    assert [(row["path"], row["count"]) for row in aggregates] == [
        (".", 2),
        ("library", 1),
    ]

    first_bytes = receipt.read_bytes()
    sentinel_mtime_ns = 1_700_000_000_000_000_000
    os.utime(receipt, ns=(sentinel_mtime_ns, sentinel_mtime_ns))
    second = _run(
        manifest,
        workspace,
        "--verify",
        "--json",
        "--receipt",
        str(receipt),
    )
    assert second.returncode == 1
    assert receipt.read_bytes() == first_bytes
    assert receipt.stat().st_mtime_ns == sentinel_mtime_ns


def test_runtime_dependency_is_locked_and_missing_dependency_is_structured(
    tmp_path: Path,
) -> None:
    lock = REQUIREMENTS.read_text(encoding="utf-8")
    assert "PyYAML==6.0.3" in lock
    assert "--no-binary=PyYAML" in lock
    assert lock.count("--hash=sha256:") == 1
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


def test_checked_manifest_budgets_three_temporary_bridge_aliases() -> None:
    data, _ = workspace_bootstrap.load_manifest(MANIFEST)
    assert data["limits"]["max_compatibility_links"] == 3
    assert len(data["migration"]["compatibility_links"]) == 3


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


def test_clone_is_noninteractive_bounded_and_times_out_as_structured_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    receipt = tmp_path / "receipts" / "clone-timeout.json"
    observed: dict[str, object] = {}

    def timed_out_run(command: list[str], **kwargs: object) -> None:
        observed["command"] = command
        observed["kwargs"] = kwargs
        raise subprocess.TimeoutExpired(
            command,
            workspace_bootstrap.CLONE_TIMEOUT_SECONDS,
        )

    monkeypatch.setattr(workspace_bootstrap.subprocess, "run", timed_out_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--json",
            "--receipt",
            str(receipt),
        ],
    )

    assert workspace_bootstrap.main() == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["error"].endswith("clone timed out")
    assert report["failed_action"]["operation"] == "clone"
    assert "Traceback" not in captured.err
    assert json.loads(receipt.read_text(encoding="utf-8"))["error"].endswith(
        "clone timed out"
    )

    assert observed["command"][:3] == ["git", "clone", "--origin"]
    kwargs = observed["kwargs"]
    assert kwargs["timeout"] == workspace_bootstrap.CLONE_TIMEOUT_SECONDS
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    env = kwargs["env"]
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_ASKPASS"] == ""
    assert env["SSH_ASKPASS"] == ""
    assert env["GCM_INTERACTIVE"] == "Never"
    assert env["GIT_OPTIONAL_LOCKS"] == "0"


@pytest.mark.parametrize(
    ("target", "target_operation"),
    [
        ("runtime/worktrees", "mkdir"),
        ("library/engine/organvm/tool", "clone"),
    ],
)
def test_first_apply_queues_compatibility_link_after_new_target_and_converges(
    tmp_path: Path,
    target: str,
    target_operation: str,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["limits"]["max_compatibility_links"] = 1
    data["migration"]["compatibility_links"] = [
        _compatibility_link("legacy-tool", target)
    ]
    _write(manifest, data)

    planned = _run(manifest, workspace, "--plan", "--json")
    assert planned.returncode == 0, planned.stdout + planned.stderr
    actions = json.loads(planned.stdout)["actions"]
    target_index = next(
        index
        for index, row in enumerate(actions)
        if row["operation"] == target_operation and row["path"] == target
    )
    link_index = next(
        index
        for index, row in enumerate(actions)
        if row["operation"] == "symlink" and row["path"] == "legacy-tool"
    )
    assert target_index < link_index

    first = _run(manifest, workspace, "--json")
    assert first.returncode == 0, first.stdout + first.stderr
    first_report = json.loads(first.stdout)
    assert first_report["actions"] == []
    assert any(
        row["operation"] == "symlink" and row["path"] == "legacy-tool"
        for row in first_report["applied"]
    )

    second = _run(manifest, workspace, "--json")
    assert second.returncode == 0, second.stdout + second.stderr
    second_report = json.loads(second.stdout)
    assert second_report["actions"] == []
    assert second_report["applied"] == []
    assert second_report["blockers"] == []


def test_planner_caps_queued_compatibility_links_at_zero_and_one(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["migration"]["compatibility_links"] = [
        _compatibility_link("legacy-a"),
        _compatibility_link("legacy-b"),
    ]

    data["limits"]["max_compatibility_links"] = 0
    _write(manifest, data)
    zero_report = json.loads(_run(manifest, workspace, "--plan", "--json").stdout)
    assert not any(row["operation"] == "symlink" for row in zero_report["actions"])
    assert [
        row["path"]
        for row in zero_report["blockers"]
        if "compatibility link limit exceeded" in row["detail"]
    ] == ["legacy-a", "legacy-b"]

    data["limits"]["max_compatibility_links"] = 1
    _write(manifest, data)
    one_report = json.loads(_run(manifest, workspace, "--plan", "--json").stdout)
    assert [
        row["path"] for row in one_report["actions"] if row["operation"] == "symlink"
    ] == ["legacy-a"]
    assert [
        row["path"]
        for row in one_report["blockers"]
        if "compatibility link limit exceeded" in row["detail"]
    ] == ["legacy-b"]


def test_existing_compatibility_link_consumes_budget_before_queued_links(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    assert _run(manifest, workspace).returncode == 0
    data = _load(manifest)
    data["limits"]["max_compatibility_links"] = 1
    data["migration"]["compatibility_links"] = [
        _compatibility_link("missing-link"),
        _compatibility_link("existing-link"),
    ]
    _write(manifest, data)
    (workspace / "existing-link").symlink_to(
        workspace / "runtime" / "worktrees",
        target_is_directory=True,
    )

    report = json.loads(_run(manifest, workspace, "--plan", "--json").stdout)

    assert not any(row["operation"] == "symlink" for row in report["actions"])
    assert any(
        row["path"] == "missing-link"
        and "compatibility link limit exceeded" in row["detail"]
        for row in report["blockers"]
    )
    assert not any(row["path"] == "existing-link" for row in report["blockers"])


def test_same_legacy_and_compatibility_path_converges_after_external_rehome(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path, include_legacy=True)
    data = _load(manifest)
    data["limits"]["max_compatibility_links"] = 1
    data["migration"]["compatibility_links"] = [
        _compatibility_link(
            "tool-old",
            target="library/engine/organvm/tool",
        )
    ]
    _write(manifest, data)
    legacy = workspace / "tool-old"
    legacy.mkdir(parents=True)
    (legacy / "preserved.txt").write_text("preserve me\n", encoding="utf-8")

    blocked = json.loads(_run(manifest, workspace, "--plan", "--json").stdout)
    assert any(
        row["path"] == "library/engine/organvm/tool"
        and "legacy source present" in row["detail"]
        for row in blocked["blockers"]
    )
    assert any(
        row["path"] == "tool-old"
        and "compatibility target is not a valid canonical row" in row["detail"]
        for row in blocked["blockers"]
    )

    rehomed = tmp_path / "external-rehome"
    legacy.rename(rehomed)
    applied = _run(manifest, workspace, "--json")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    canonical = workspace / "library" / "engine" / "organvm" / "tool"
    assert canonical.is_dir()
    assert legacy.is_symlink()
    assert legacy.resolve(strict=True) == canonical.resolve(strict=True)
    assert (rehomed / "preserved.txt").read_text(encoding="utf-8") == "preserve me\n"

    second = json.loads(_run(manifest, workspace, "--json").stdout)
    assert second["actions"] == []
    assert second["applied"] == []
    assert second["blockers"] == []


def test_scan_error_is_one_structured_unmeasured_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    assert _run(manifest, workspace).returncode == 0
    receipt = tmp_path / "receipts" / "scan-error.json"
    real_scandir = os.scandir

    def guarded_scandir(path: str | os.PathLike[str]) -> os.ScandirIterator[str]:
        if Path(path) == workspace / "runtime":
            raise PermissionError("host-specific scan error")
        return real_scandir(path)

    monkeypatch.setattr(workspace_bootstrap.os, "scandir", guarded_scandir)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--verify",
            "--json",
            "--receipt",
            str(receipt),
        ],
    )

    assert workspace_bootstrap.main() == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    scan_failures = [
        row
        for row in report["failures"]
        if row["detail"] == "directory scan failed; Workspace parity is unmeasured"
    ]
    assert scan_failures == [
        {
            "detail": "directory scan failed; Workspace parity is unmeasured",
            "operation": "verify-unmeasured",
            "path": "runtime",
        }
    ]
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert stored["failures"] == report["failures"]
    assert stored["workspace_root"] == "$WORKSPACE_ROOT"
    assert "Traceback" not in captured.err
    assert "host-specific scan error" not in json.dumps(report)


def test_compatibility_link_limit_counts_only_present_valid_aliases(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["limits"]["max_compatibility_links"] = 1
    data["migration"]["compatibility_links"] = [
        _compatibility_link("legacy/runtime-old")
    ]
    _write(manifest, data)

    applied = _run(manifest, workspace, "--json")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    allowed = _run(manifest, workspace, "--verify", "--json")
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert json.loads(allowed.stdout)["failures"] == []

    alias = workspace / "legacy" / "runtime-old"
    alias.unlink()
    alias.parent.rmdir()
    absent = _run(manifest, workspace, "--verify", "--json")
    assert absent.returncode == 0, absent.stdout + absent.stderr
    assert json.loads(absent.stdout)["actions"] == []

    alias.parent.mkdir()
    alias.symlink_to(workspace / "runtime" / "worktrees", target_is_directory=True)
    data["limits"]["max_compatibility_links"] = 0
    _write(manifest, data)
    over_limit = _run(manifest, workspace, "--verify", "--json")
    assert over_limit.returncode == 1
    assert any(
        row["detail"] == "present compatibility links exceed declared limit: 1 > 0"
        for row in json.loads(over_limit.stdout)["failures"]
    )

    alias.unlink()
    alias.symlink_to(workspace / "runtime", target_is_directory=True)
    data["limits"]["max_compatibility_links"] = 1
    _write(manifest, data)
    wrong = _run(manifest, workspace, "--verify", "--json")
    wrong_failures = json.loads(wrong.stdout)["failures"]
    assert wrong.returncode == 1
    assert any(
        row["path"] == "legacy/runtime-old"
        and row["detail"] == "compatibility link does not target runtime/worktrees"
        for row in wrong_failures
    )
    assert not any("exceed declared limit" in row["detail"] for row in wrong_failures)

    alias.unlink()
    alias.symlink_to(workspace / "runtime" / "worktrees", target_is_directory=True)
    data["migration"]["compatibility_links"][0]["expires_at"] = "2000-01-01T00:00:00Z"
    _write(manifest, data)
    expired = _run(manifest, workspace, "--verify", "--json")
    expired_failures = json.loads(expired.stdout)["failures"]
    assert expired.returncode == 1
    assert any(
        row["path"] == "legacy/runtime-old" and "expired" in row["detail"]
        for row in expired_failures
    )
    assert not any("exceed declared limit" in row["detail"] for row in expired_failures)


@pytest.mark.parametrize(
    "paths",
    [
        ("legacy", "legacy/sub"),
        ("legacy/sub", "legacy"),
    ],
)
def test_nested_compatibility_paths_are_rejected_in_either_order(
    tmp_path: Path,
    paths: tuple[str, str],
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["migration"]["compatibility_links"] = [
        _compatibility_link(path) for path in paths
    ]
    _write(manifest, data)

    proc = _run(manifest, workspace, "--plan", "--json")
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "nested compatibility paths are not allowed" in report["error"]
    assert "Traceback" not in proc.stderr


@pytest.mark.parametrize(
    "paths",
    [
        ("legacy/a", "legacy/b"),
        ("legacy", "legacy-old"),
    ],
)
def test_sibling_compatibility_path_prefixes_remain_valid(
    tmp_path: Path,
    paths: tuple[str, str],
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["limits"]["max_compatibility_links"] = len(paths)
    data["migration"]["compatibility_links"] = [
        _compatibility_link(path) for path in paths
    ]
    _write(manifest, data)

    proc = _run(manifest, workspace, "--plan", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert "error" not in report
    assert {
        row["path"] for row in report["actions"] if row["operation"] == "symlink"
    } == set(paths)


@pytest.mark.parametrize("probe", ["is_file", "read_bytes"])
def test_manifest_filesystem_errors_are_structured_and_receipted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    probe: str,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    receipt = tmp_path / "receipts" / f"manifest-{probe}.json"
    injected = "host-private manifest failure"
    if probe == "is_file":
        real_is_file = Path.is_file

        def guarded_is_file(path: Path) -> bool:
            if path == manifest:
                raise PermissionError(injected)
            return real_is_file(path)

        monkeypatch.setattr(Path, "is_file", guarded_is_file)
    else:
        real_read_bytes = Path.read_bytes

        def guarded_read_bytes(path: Path) -> bytes:
            if path == manifest:
                raise PermissionError(injected)
            return real_read_bytes(path)

        monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--plan",
            "--json",
            "--receipt",
            str(receipt),
        ],
    )

    assert workspace_bootstrap.main() == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert stored == report
    assert report["error"].endswith("PermissionError")
    assert injected not in json.dumps(report)
    assert "Traceback" not in captured.err
    assert not workspace.exists()


def test_filesystem_root_is_rejected_before_apply(
    tmp_path: Path,
) -> None:
    manifest, _, _ = _manifest(tmp_path)
    data = _load(manifest)
    unique = f"portvs-root-guard-{os.getpid()}-{tmp_path.name}"
    data["rows"] = [
        {
            "path": unique,
            "kind": "structural",
            "owner_ref": "portvs",
            "residency": "structural",
        }
    ]
    data["migration"]["compatibility_links"] = []
    _write(manifest, data)
    forbidden_target = Path("/") / unique
    assert not forbidden_target.exists()
    receipt = tmp_path / "receipts" / "root-guard.json"

    proc = _run(
        manifest,
        Path("/"),
        "--json",
        "--receipt",
        str(receipt),
    )

    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "filesystem root" in report["error"]
    assert json.loads(receipt.read_text(encoding="utf-8")) == report
    assert "Traceback" not in proc.stderr
    assert not forbidden_target.exists()


def test_root_validation_rejects_home_ancestors_but_accepts_descendants(
    tmp_path: Path,
) -> None:
    for unsafe in (Path.home(), Path.home().parent):
        with pytest.raises(workspace_bootstrap.ContractError, match="home-directory"):
            workspace_bootstrap.resolve_root(
                {"workspace_root": str(unsafe)},
                None,
            )
    safe = tmp_path / "Workspace"
    assert (
        workspace_bootstrap.resolve_root(
            {"workspace_root": str(safe)},
            None,
        )
        == safe
    )


def test_legacy_path_cannot_collide_with_a_later_managed_row(
    tmp_path: Path,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    repository = next(row for row in data["rows"] if row["kind"] == "repository")
    repository["legacy_paths"] = ["runtime/worktrees"]
    _write(manifest, data)
    receipt = tmp_path / "receipts" / "legacy-collision.json"

    proc = _run(
        manifest,
        workspace,
        "--plan",
        "--json",
        "--receipt",
        str(receipt),
    )

    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "legacy path collides with managed row runtime/worktrees" in report["error"]
    assert json.loads(receipt.read_text(encoding="utf-8")) == report
    assert "Traceback" not in proc.stderr
    assert not workspace.exists()


def _index_action_data() -> tuple[dict[str, object], workspace_bootstrap.Action]:
    row = {
        "path": "archive-index.json",
        "kind": "index",
        "source_ref": "https://example.invalid/archives",
        "generator": "jack.sh --refresh-index",
    }
    return (
        {"rows": [row]},
        workspace_bootstrap.Action(
            "write-index",
            "archive-index.json",
            str(row["source_ref"]),
        ),
    )


def test_index_publication_partial_write_leaves_no_canonical_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "Workspace"
    root.mkdir()
    data, action = _index_action_data()
    real_write = os.write
    writes = 0

    def partial_then_fail(fd: int, payload: bytes) -> int:
        nonlocal writes
        writes += 1
        if writes == 1:
            return real_write(fd, payload[: max(1, len(payload) // 2)])
        raise OSError("host-private disk detail")

    monkeypatch.setattr(workspace_bootstrap.os, "write", partial_then_fail)

    with pytest.raises(workspace_bootstrap.ApplyError) as raised:
        workspace_bootstrap.apply_actions(data, root, [action])

    assert raised.value.applied == []
    assert raised.value.failed_action == action
    assert str(raised.value).endswith("OSError")
    assert "host-private disk detail" not in str(raised.value)
    assert not (root / action.path).exists()
    assert list(root.glob(".archive-index.json.*.tmp")) == []


def test_index_publication_race_never_replaces_the_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "Workspace"
    root.mkdir()
    data, action = _index_action_data()
    winner = b"race winner\n"

    def racing_link(source: Path, destination: Path) -> None:
        del source
        Path(destination).write_bytes(winner)
        raise FileExistsError("destination appeared")

    monkeypatch.setattr(workspace_bootstrap.os, "link", racing_link)

    with pytest.raises(workspace_bootstrap.ApplyError) as raised:
        workspace_bootstrap.apply_actions(data, root, [action])

    assert raised.value.applied == []
    assert raised.value.failed_action == action
    assert "bootstrap never overwrites" in str(raised.value)
    assert (root / action.path).read_bytes() == winner
    assert list(root.glob(".archive-index.json.*.tmp")) == []


def test_index_publication_is_same_directory_and_durable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "Workspace"
    root.mkdir()
    data, action = _index_action_data()
    real_mkstemp = workspace_bootstrap.tempfile.mkstemp
    real_fsync = workspace_bootstrap.os.fsync
    temp_directories: list[Path] = []
    fsynced: list[int] = []

    def observed_mkstemp(*args: object, **kwargs: object) -> tuple[int, str]:
        temp_directories.append(Path(str(kwargs["dir"])))
        return real_mkstemp(*args, **kwargs)

    def observed_fsync(fd: int) -> None:
        fsynced.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(workspace_bootstrap.tempfile, "mkstemp", observed_mkstemp)
    monkeypatch.setattr(workspace_bootstrap.os, "fsync", observed_fsync)

    assert workspace_bootstrap.apply_actions(data, root, [action]) == [action]

    target = root / action.path
    assert target.read_bytes() == workspace_bootstrap._index_bytes(data["rows"][0])
    assert temp_directories == [root]
    assert len(fsynced) == 2
    assert list(root.glob(".archive-index.json.*.tmp")) == []


def test_unreadable_index_is_a_bounded_blocker_and_unmeasured_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    assert _run(manifest, workspace).returncode == 0
    index = workspace / "library" / "underworld" / "archive-index.json"
    receipt = tmp_path / "receipts" / "unreadable-index.json"
    real_read_bytes = Path.read_bytes
    injected = "host-private index failure"

    def guarded_read_bytes(path: Path) -> bytes:
        if path == index:
            raise PermissionError(injected)
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--verify",
            "--json",
            "--receipt",
            str(receipt),
        ],
    )

    assert workspace_bootstrap.main() == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert any(
        row["path"] == "library/underworld/archive-index.json"
        and row["detail"] == "index cannot be read: PermissionError"
        for row in report["blockers"]
    )
    assert [
        row
        for row in report["failures"]
        if row["path"] == "library/underworld/archive-index.json"
        and row["operation"] == "verify-unmeasured"
    ] == [
        {
            "detail": (
                "index content cannot be read; parity is unmeasured: PermissionError"
            ),
            "operation": "verify-unmeasured",
            "path": "library/underworld/archive-index.json",
        }
    ]
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert any(
        row["path"] == "library/underworld/archive-index.json"
        and row["operation"] == "verify-unmeasured"
        for row in stored["failures"]
    )
    assert injected not in json.dumps(report)
    assert "Traceback" not in captured.err


def test_resolution_runtime_error_is_structured_in_plan_and_verify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["limits"]["max_compatibility_links"] = 1
    data["migration"]["compatibility_links"] = [_compatibility_link("runtime-old")]
    _write(manifest, data)
    assert _run(manifest, workspace).returncode == 0
    alias = workspace / "runtime-old"
    receipt = tmp_path / "receipts" / "resolution-loop.json"
    real_resolve = Path.resolve

    def guarded_resolve(path: Path, strict: bool = False) -> Path:
        if path == alias:
            raise RuntimeError("host-private symlink loop")
        return real_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", guarded_resolve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--verify",
            "--json",
            "--receipt",
            str(receipt),
        ],
    )

    assert workspace_bootstrap.main() == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert any(
        row["path"] == "runtime-old"
        and row["detail"] == ("compatibility link cannot be resolved: RuntimeError")
        for row in report["blockers"]
    )
    assert any(
        row["path"] == "runtime-old"
        and row["operation"] == "verify-unmeasured"
        and row["detail"]
        == ("compatibility link target cannot be resolved: RuntimeError")
        for row in report["failures"]
    )
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert any(
        row["path"] == "runtime-old" and row["operation"] == "verify-unmeasured"
        for row in stored["failures"]
    )
    assert "host-private symlink loop" not in json.dumps(report)
    assert "Traceback" not in captured.err


def test_safe_destination_converts_resolution_runtime_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "Workspace"
    root.mkdir()
    loop = root / "loop"
    loop.symlink_to(loop, target_is_directory=True)
    real_resolve = Path.resolve

    def guarded_resolve(path: Path, strict: bool = False) -> Path:
        if path == loop:
            raise RuntimeError("host-private symlink loop")
        return real_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", guarded_resolve)

    with pytest.raises(
        workspace_bootstrap.ResolutionError,
        match="symlink component cannot be resolved: RuntimeError",
    ):
        workspace_bootstrap._safe_destination(root, "loop/child")


@pytest.mark.parametrize(
    ("compatibility_path", "expected_kind"),
    [
        ("library/engine/organvm/tool/alias", "repository"),
        ("runtime/worktrees/alias", "ephemeral"),
        ("secrets/alias", "private"),
        ("library/underworld/archive-index.json/alias", "index"),
    ],
)
def test_compatibility_path_cannot_enter_non_structural_managed_interiors(
    tmp_path: Path,
    compatibility_path: str,
    expected_kind: str,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    if expected_kind == "private":
        data["rows"].append(
            {
                "path": "secrets",
                "kind": "private",
                "owner_ref": "private-inventory",
                "residency": "private",
                "custody_label": "workspace-private",
                "sealed_inventory_ref": "receipt://sealed",
                "restoration_receipt_ref": "receipt://restored",
            }
        )
    data["migration"]["compatibility_links"] = [_compatibility_link(compatibility_path)]
    _write(manifest, data)

    proc = _run(manifest, workspace, "--plan", "--json")

    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert f"beneath declared {expected_kind} row" in report["error"]
    assert "Traceback" not in proc.stderr
    assert not workspace.exists()


@pytest.mark.parametrize("field", ["max_violations", "max_unmeasured"])
def test_exact_convergence_limits_reject_nonzero_values(
    tmp_path: Path,
    field: str,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    data["limits"][field] = 1
    _write(manifest, data)

    proc = _run(manifest, workspace, "--plan", "--json")

    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert report["error"] == (
        f"limits.{field} must be 0 for exact Workspace convergence"
    )
    assert "Traceback" not in proc.stderr
    assert not workspace.exists()


def test_exact_convergence_limits_accept_zero(tmp_path: Path) -> None:
    manifest, _, _ = _manifest(tmp_path)
    data, _ = workspace_bootstrap.load_manifest(manifest)
    assert data["limits"]["max_violations"] == 0
    assert data["limits"]["max_unmeasured"] == 0


@pytest.mark.parametrize(
    "surface",
    [
        "row",
        "compatibility_path",
        "compatibility_target",
    ],
)
def test_nul_paths_are_structured_contract_errors_without_root_creation(
    tmp_path: Path,
    surface: str,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    data = _load(manifest)
    if surface == "row":
        data["rows"][0]["path"] = "bad\0name"
    else:
        link = _compatibility_link("runtime-old")
        field = "path" if surface == "compatibility_path" else "target"
        link[field] = f"bad\0{field}"
        data["migration"]["compatibility_links"] = [link]
    _write(manifest, data)
    receipt = tmp_path / "receipts" / f"nul-{surface}.json"

    proc = _run(
        manifest,
        workspace,
        "--json",
        "--receipt",
        str(receipt),
    )

    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "invalid relative path" in report["error"]
    assert json.loads(receipt.read_text(encoding="utf-8")) == report
    assert "Traceback" not in proc.stderr
    assert not workspace.exists()


@pytest.mark.parametrize("stage", ["directory", "open", "write"])
def test_receipt_preflight_failure_prevents_apply_mutations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stage: str,
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    receipt = tmp_path / f"receipts-{stage}" / "preflight.json"
    real_mkdir = Path.mkdir
    real_mkstemp = workspace_bootstrap.tempfile.mkstemp
    real_write = workspace_bootstrap.os.write

    def guarded_mkdir(path: Path, *args: object, **kwargs: object) -> None:
        if stage == "directory" and path == receipt.parent:
            raise PermissionError("host-private receipt directory")
        real_mkdir(path, *args, **kwargs)

    def preflight_failure(*args: object, **kwargs: object) -> tuple[int, str]:
        if stage == "open" and ".preflight-" in str(kwargs.get("prefix")):
            raise PermissionError("host-private receipt preflight")
        return real_mkstemp(*args, **kwargs)

    def guarded_write(fd: int, payload: bytes) -> int:
        if stage == "write" and payload.startswith(b"portvs receipt preflight"):
            raise PermissionError("host-private receipt write")
        return real_write(fd, payload)

    monkeypatch.setattr(Path, "mkdir", guarded_mkdir)
    monkeypatch.setattr(workspace_bootstrap.tempfile, "mkstemp", preflight_failure)
    monkeypatch.setattr(workspace_bootstrap.os, "write", guarded_write)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--json",
            "--receipt",
            str(receipt),
        ],
    )

    assert workspace_bootstrap.main() == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["error"] == "receipt preflight failed: PermissionError"
    assert "host-private receipt preflight" not in json.dumps(report)
    assert "Traceback" not in captured.err
    assert not workspace.exists()
    assert not receipt.exists()


def test_receipt_write_race_preserves_post_apply_evidence_in_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest, workspace, _ = _manifest(tmp_path)
    receipt = tmp_path / "receipts" / "write-race.json"
    real_write_text = Path.write_text

    def guarded_write_text(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == receipt:
            raise PermissionError("host-private receipt race")
        return real_write_text(
            path,
            data,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

    monkeypatch.setattr(Path, "write_text", guarded_write_text)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(BOOTSTRAP),
            "--manifest",
            str(manifest),
            "--root",
            str(workspace),
            "--json",
            "--receipt",
            str(receipt),
        ],
    )

    assert workspace_bootstrap.main() == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["ok"] is False
    assert report["error"] == "receipt write failed: PermissionError"
    assert report["receipt_error"] == report["error"]
    assert report["applied"]
    assert "host-private receipt race" not in json.dumps(report)
    assert "Traceback" not in captured.err
    assert workspace.is_dir()
    assert (workspace / "library" / "underworld" / "archive-index.json").is_file()
    assert not receipt.exists()


def test_checked_apply_receipts_distinguish_historical_and_current_evidence() -> None:
    manifest_digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    historical = json.loads(HISTORICAL_APPLY_RECEIPT.read_text(encoding="utf-8"))
    current = json.loads(LIVE_APPLY_RECEIPT.read_text(encoding="utf-8"))
    plan = json.loads(LIVE_PLAN_RECEIPT.read_text(encoding="utf-8"))
    verified = json.loads(LIVE_VERIFY_RECEIPT.read_text(encoding="utf-8"))

    assert historical["mode"] == "apply"
    assert historical["applied"]
    assert historical["manifest_sha256"] != manifest_digest
    assert current["mode"] == "apply"
    assert current["manifest_sha256"] == manifest_digest
    assert current["actions"] == []
    assert current["applied"] == []
    assert current["blockers"] == plan["blockers"]
    assert plan["actions"] == []
    assert {
        current["manifest_sha256"],
        plan["manifest_sha256"],
        verified["manifest_sha256"],
    } == {manifest_digest}


def test_jack_has_one_final_newline_without_a_blank_line() -> None:
    content = JACK.read_bytes()
    assert content.endswith(b'"$@"\n')
    assert not content.endswith(b"\n\n")
