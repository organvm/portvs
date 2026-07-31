from __future__ import annotations

import json
from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[1]
JACK = ROOT / "jack.sh"


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
