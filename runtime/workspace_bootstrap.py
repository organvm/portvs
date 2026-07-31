#!/usr/bin/env python3
"""Additively materialize PORTVS's literal Workspace manifest.

The bootstrap creates missing containers, reproducible index files, repositories
whose canonical destination and every declared legacy source are absent, and
temporary compatibility links whose source path is absent.  It never moves,
overwrites, or deletes.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
from typing import Any, Mapping
from urllib.parse import urlparse

try:
    import yaml
except (
    ModuleNotFoundError
):  # pragma: no cover - exercised in a dependency-free subprocess
    yaml = None


SCHEMA = "portvs.workspace_manifest.v1"
REPORT_SCHEMA = "portvs.workspace_bootstrap_report.v1"
KINDS = {"structural", "repository", "private", "ephemeral", "index"}
DIRECTORY_KINDS = {"structural", "repository", "private", "ephemeral"}


class ContractError(ValueError):
    pass


class ApplyError(ContractError):
    def __init__(
        self,
        message: str,
        applied: list["Action"],
        failed_action: "Action | None" = None,
    ) -> None:
        super().__init__(message)
        self.applied = list(applied)
        self.failed_action = failed_action


@dataclass(frozen=True)
class Action:
    operation: str
    path: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"operation": self.operation, "path": self.path, "detail": self.detail}


def _safe_path(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise ContractError(f"invalid relative path: {value!r}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ContractError(f"unsafe relative path: {value!r}")
    if pure.as_posix() != value.rstrip("/"):
        raise ContractError(f"non-normalized relative path: {value!r}")
    return pure.as_posix()


def _required_string(row: Mapping[str, Any], field: str, label: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} is missing {field}")
    return value


def _parse_deadline(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} is missing expires_at")
    normalized = value.replace("Z", "+00:00")
    try:
        deadline = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ContractError(f"{label} has invalid expires_at: {value!r}") from exc
    if deadline.tzinfo is None:
        raise ContractError(f"{label} expires_at must include a timezone")
    return deadline.astimezone(timezone.utc)


def load_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    if not path.is_file():
        raise ContractError(f"manifest missing: {path}")
    if yaml is None:
        raise ContractError(
            "PyYAML 6.0.3 is required; install the locked runtime dependency with "
            "`python3 -m pip install --require-hashes -r requirements.txt`"
        )
    raw = path.read_bytes()
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ContractError(f"manifest YAML is invalid: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ContractError(f"manifest schema must be {SCHEMA}")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ContractError("manifest rows must be a non-empty list")
    seen: set[str] = set()
    row_by_path: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ContractError(f"rows[{index}] must be a mapping")
        for field in ("path", "kind", "owner_ref", "residency"):
            _required_string(row, field, f"rows[{index}]")
        rel = _safe_path(row["path"])
        if rel in seen:
            raise ContractError(f"duplicate manifest path: {rel}")
        seen.add(rel)
        row_by_path[rel] = row
        if row["kind"] not in KINDS:
            raise ContractError(f"{rel}: unsupported kind {row['kind']!r}")
        kind = row["kind"]
        required_by_kind = {
            "repository": ("remote", "custody_ref"),
            "private": (
                "custody_label",
                "sealed_inventory_ref",
                "restoration_receipt_ref",
            ),
            "ephemeral": ("reaper",),
            "index": ("source_ref", "generator"),
        }
        for field in required_by_kind.get(kind, ()):
            _required_string(row, field, rel)
        if kind == "repository" and not str(row["custody_ref"]).startswith("refs/"):
            raise ContractError(f"{rel}: custody_ref must begin with refs/")
        if kind == "ephemeral":
            expires_after = row.get("expires_after")
            if (
                not isinstance(expires_after, int)
                or isinstance(expires_after, bool)
                or expires_after <= 0
            ):
                raise ContractError(f"{rel}: expires_after must be a positive integer")
        legacy_paths = row.get("legacy_paths") or []
        if not isinstance(legacy_paths, list):
            raise ContractError(f"{rel}: legacy_paths must be a list")
        for legacy in legacy_paths:
            _safe_path(legacy)
    for rel, row in row_by_path.items():
        parent = PurePosixPath(rel).parent
        if str(parent) == ".":
            continue
        parent_rel = parent.as_posix()
        parent_row = row_by_path.get(parent_rel)
        if parent_row is None:
            raise ContractError(f"{rel}: undeclared parent {parent_rel}")
        if parent_row["kind"] != "structural":
            raise ContractError(
                f"{rel}: parent {parent_rel} must be a structural container"
            )
    limits = data.get("limits")
    if not isinstance(limits, dict):
        raise ContractError("limits must be a mapping")
    max_scan_entries = limits.get("max_scan_entries")
    if (
        not isinstance(max_scan_entries, int)
        or isinstance(max_scan_entries, bool)
        or max_scan_entries <= 0
    ):
        raise ContractError("limits.max_scan_entries must be a positive integer")
    for field in (
        "max_violations",
        "max_unmeasured",
        "max_compatibility_links",
    ):
        value = limits.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ContractError(f"limits.{field} must be a non-negative integer")
    migration = data.get("migration") or {}
    if not isinstance(migration, dict):
        raise ContractError("migration must be a mapping")
    links = migration.get("compatibility_links") or []
    if not isinstance(links, list):
        raise ContractError("migration.compatibility_links must be a list")
    compatibility_paths: set[str] = set()
    for index, row in enumerate(links):
        if not isinstance(row, dict):
            raise ContractError("compatibility link rows must be mappings")
        label = f"migration.compatibility_links[{index}]"
        for field in ("path", "target", "owner_ref", "expires_at"):
            _required_string(row, field, label)
        rel = _safe_path(row["path"])
        target_rel = _safe_path(row["target"])
        if rel in compatibility_paths:
            raise ContractError(f"duplicate compatibility path: {rel}")
        rel_path = PurePosixPath(rel)
        for other in compatibility_paths:
            other_path = PurePosixPath(other)
            if rel_path in other_path.parents or other_path in rel_path.parents:
                raise ContractError(
                    f"nested compatibility paths are not allowed: {other} and {rel}"
                )
        compatibility_paths.add(rel)
        if rel in row_by_path:
            raise ContractError(
                f"{rel}: compatibility path collides with a manifest row"
            )
        target_row = row_by_path.get(target_rel)
        if target_row is None or target_row["kind"] not in DIRECTORY_KINDS:
            raise ContractError(
                f"{rel}: compatibility target must be a declared directory row"
            )
        _parse_deadline(row["expires_at"], rel)
    return data, raw


def resolve_root(data: Mapping[str, Any], override: Path | None) -> Path:
    if override is not None:
        root = override.expanduser()
    else:
        value = data.get("workspace_root")
        if not isinstance(value, str) or not value:
            raise ContractError("workspace_root must be a non-empty path")
        root = Path(os.path.expandvars(value)).expanduser()
    if not root.is_absolute():
        raise ContractError(f"workspace root must be absolute: {root}")
    return Path(os.path.abspath(root))


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_destination(
    root: Path, rel: str, *, allow_final_symlink: bool = False
) -> Path:
    candidate = root / rel
    cursor = root
    parts = PurePosixPath(rel).parts
    for index, part in enumerate(parts):
        cursor = cursor / part
        is_final = index == len(parts) - 1
        if cursor.is_symlink():
            if is_final and allow_final_symlink:
                continue
            target = cursor.resolve(strict=False)
            if not _inside(target, root):
                raise ContractError(
                    f"{rel}: symlink component escapes Workspace: {cursor}"
                )
            raise ContractError(
                f"{rel}: canonical entries cannot traverse a symlink: {cursor}"
            )
        if not is_final and cursor.exists() and not cursor.is_dir():
            raise ContractError(
                f"{rel}: path component is not a physical directory: {cursor}"
            )
    return candidate


def _index_bytes(row: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            {
                "schema": "portvs.remote_archive_index_pointer.v1",
                "source_ref": row["source_ref"],
                "generator": row["generator"],
                "note": "Remote/archive index only. Archived repositories are not hydrated here.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _canonical_remote(value: str) -> str:
    text = value.strip()
    if text.startswith("git@github.com:"):
        text = "https://github.com/" + text.removeprefix("git@github.com:")
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc.lower() == "github.com":
        path = parsed.path.strip("/")
        return "https://github.com/" + path.removesuffix(".git").lower()
    if text.startswith("file://"):
        return str(Path(parsed.path).resolve(strict=False))
    path = Path(text).expanduser()
    return (
        str(path.resolve(strict=False))
        if path.is_absolute()
        else text.removesuffix(".git")
    )


def _repo_matches(path: Path, row: Mapping[str, Any]) -> bool:
    if not (path / ".git").exists():
        return False
    proc = subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if proc.returncode != 0 or _canonical_remote(
        proc.stdout.strip()
    ) != _canonical_remote(str(row["remote"])):
        return False
    custody = subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "show-ref",
            "--verify",
            "--quiet",
            str(row["custody_ref"]),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    return custody.returncode == 0


def _blocked_ancestor(rel: str, status: Mapping[str, bool]) -> str | None:
    parent = PurePosixPath(rel).parent
    while str(parent) != ".":
        parent_rel = parent.as_posix()
        if status.get(parent_rel) is False:
            return parent_rel
        parent = parent.parent
    return None


def _private_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def plan(data: Mapping[str, Any], root: Path) -> tuple[list[Action], list[Action]]:
    actions: list[Action] = []
    blockers: list[Action] = []
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        return (
            actions,
            [
                Action(
                    "blocked",
                    ".",
                    "Workspace root must be a physical directory",
                )
            ],
        )
    canonical_status: dict[str, bool] = {}
    rows = sorted(
        data["rows"],
        key=lambda row: (len(PurePosixPath(row["path"]).parts), row["path"]),
    )
    for row in rows:
        rel = _safe_path(row["path"])
        if ancestor := _blocked_ancestor(rel, canonical_status):
            blockers.append(
                Action("blocked", rel, f"declared ancestor is blocked: {ancestor}")
            )
            canonical_status[rel] = False
            continue
        try:
            path = _safe_destination(root, rel)
        except ContractError as exc:
            blockers.append(Action("blocked", rel, str(exc)))
            canonical_status[rel] = False
            continue
        kind = row["kind"]
        if kind in {"structural", "private", "ephemeral"}:
            if path.exists():
                if not path.is_dir() or path.is_symlink():
                    blockers.append(
                        Action("blocked", rel, f"{kind} requires a physical directory")
                    )
                    canonical_status[rel] = False
                    continue
                if kind == "private" and _private_mode(path) != 0o700:
                    actions.append(
                        Action(
                            "chmod-private",
                            rel,
                            "set declared private container mode to 0700",
                        )
                    )
            else:
                actions.append(
                    Action("mkdir", rel, f"create declared {kind} container")
                )
            canonical_status[rel] = True
        elif kind == "index":
            desired = _index_bytes(row)
            if path.exists():
                if not path.is_file() or path.is_symlink():
                    blockers.append(
                        Action("blocked", rel, "index path is not a physical file")
                    )
                    canonical_status[rel] = False
                elif path.read_bytes() != desired:
                    blockers.append(
                        Action(
                            "blocked",
                            rel,
                            "existing index differs; bootstrap never overwrites",
                        )
                    )
                    canonical_status[rel] = False
                else:
                    canonical_status[rel] = True
            else:
                actions.append(Action("write-index", rel, str(row["source_ref"])))
                canonical_status[rel] = True
        elif kind == "repository":
            if path.exists():
                if (
                    not path.is_dir()
                    or path.is_symlink()
                    or not _repo_matches(path, row)
                ):
                    blockers.append(
                        Action(
                            "blocked",
                            rel,
                            "existing path is not the declared repository",
                        )
                    )
                    canonical_status[rel] = False
                else:
                    canonical_status[rel] = True
                continue
            legacy = [
                legacy_rel
                for legacy_rel in row.get("legacy_paths") or []
                if (root / _safe_path(legacy_rel)).exists()
                or (root / _safe_path(legacy_rel)).is_symlink()
            ]
            if legacy:
                blockers.append(
                    Action(
                        "blocked",
                        rel,
                        "legacy source present; preserve/rehome it before hydration: "
                        + ", ".join(legacy),
                    )
                )
                canonical_status[rel] = False
            else:
                actions.append(Action("clone", rel, str(row["remote"])))
                canonical_status[rel] = True

    migration = data.get("migration") or {}
    for row in migration.get("compatibility_links") or []:
        rel = _safe_path(row["path"])
        target_rel = _safe_path(row["target"])
        if _parse_deadline(row["expires_at"], rel) <= datetime.now(timezone.utc):
            blockers.append(
                Action(
                    "blocked",
                    rel,
                    f"compatibility link expired at {row['expires_at']}",
                )
            )
            continue
        try:
            path = _safe_destination(root, rel, allow_final_symlink=True)
            target = _safe_destination(root, target_rel)
        except ContractError as exc:
            blockers.append(Action("blocked", rel, str(exc)))
            continue
        if canonical_status.get(target_rel) is not True:
            blockers.append(
                Action(
                    "blocked",
                    rel,
                    f"compatibility target is not a valid canonical row: {target_rel}",
                )
            )
            continue
        if path.exists() or path.is_symlink():
            if not path.is_symlink() or path.resolve(strict=False) != target.resolve(
                strict=False
            ):
                blockers.append(
                    Action(
                        "blocked",
                        rel,
                        f"occupied compatibility path; target is {target_rel}",
                    )
                )
        else:
            actions.append(Action("symlink", rel, target_rel))
    return actions, blockers


def _row_by_path(data: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(row["path"]): row for row in data["rows"]}


def apply_actions(
    data: Mapping[str, Any], root: Path, actions: list[Action]
) -> list[Action]:
    applied: list[Action] = []
    rows = _row_by_path(data)
    try:
        if not root.exists():
            root.mkdir(parents=True)
            applied.append(Action("mkdir-root", ".", "create Workspace root"))
        elif not root.is_dir() or root.is_symlink():
            raise ContractError("Workspace root must be a physical directory")
    except (ContractError, OSError) as exc:
        raise ApplyError(str(exc), applied) from exc

    for action in actions:
        try:
            path = _safe_destination(root, action.path)
            if action.operation == "mkdir":
                row = rows[action.path]
                path.mkdir(mode=0o700 if row["kind"] == "private" else 0o777)
                if row["kind"] == "private":
                    path.chmod(0o700)
            elif action.operation == "chmod-private":
                path.chmod(0o700)
            elif action.operation == "write-index":
                path.write_bytes(_index_bytes(rows[action.path]))
            elif action.operation == "clone":
                row = rows[action.path]
                command = ["git", "clone", "--origin", "origin"]
                if branch := row.get("default_branch"):
                    command.extend(["--branch", str(branch), "--single-branch"])
                command.extend([str(row["remote"]), str(path)])
                proc = subprocess.run(
                    command, capture_output=True, text=True, check=False
                )
                if proc.returncode != 0:
                    raise ContractError(
                        f"{action.path}: clone failed: {proc.stderr.strip()[:500]}"
                    )
                if not _repo_matches(path, row):
                    applied.append(action)
                    raise ContractError(
                        f"{action.path}: cloned repository lacks its declared custody_ref"
                    )
            elif action.operation == "symlink":
                target = _safe_destination(root, action.detail)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(target, target_is_directory=True)
            else:
                raise ContractError(f"unsupported action: {action.operation}")
            applied.append(action)
        except (ContractError, OSError) as exc:
            raise ApplyError(str(exc), applied, action) from exc
    return applied


def verify(data: Mapping[str, Any], root: Path) -> list[Action]:
    failures: list[Action] = []
    rows = _row_by_path(data)
    if not root.is_dir() or root.is_symlink():
        return [
            Action(
                "verify-fail",
                ".",
                "Workspace root is absent or not a physical directory",
            )
        ]
    safe_paths: dict[str, Path] = {}
    unsafe: dict[str, str] = {}
    for rel in sorted(rows, key=lambda value: (len(PurePosixPath(value).parts), value)):
        if ancestor := _blocked_ancestor(rel, {path: False for path in unsafe}):
            unsafe[rel] = f"declared ancestor is unsafe: {ancestor}"
            continue
        try:
            safe_paths[rel] = _safe_destination(root, rel)
        except ContractError as exc:
            unsafe[rel] = str(exc)
            failures.append(Action("verify-fail", rel, str(exc)))

    valid_compatibility_paths: set[str] = set()
    valid_compatibility_links = 0
    links = (data.get("migration") or {}).get("compatibility_links") or []
    now = datetime.now(timezone.utc)
    for row in links:
        rel = _safe_path(row["path"])
        target_rel = _safe_path(row["target"])
        try:
            path = _safe_destination(root, rel, allow_final_symlink=True)
        except ContractError as exc:
            failures.append(Action("verify-fail", rel, str(exc)))
            continue
        if not path.exists() and not path.is_symlink():
            continue
        if _parse_deadline(row["expires_at"], rel) <= now:
            failures.append(
                Action(
                    "verify-fail",
                    rel,
                    f"compatibility link expired at {row['expires_at']}",
                )
            )
            continue
        try:
            target = _safe_destination(root, target_rel)
        except ContractError as exc:
            failures.append(Action("verify-fail", rel, str(exc)))
            continue
        if target_rel in unsafe or not target.is_dir() or target.is_symlink():
            failures.append(
                Action(
                    "verify-fail",
                    rel,
                    f"compatibility target is not a valid canonical row: {target_rel}",
                )
            )
            continue
        if not path.is_symlink():
            failures.append(
                Action(
                    "verify-fail",
                    rel,
                    f"compatibility path is not a symlink to {target_rel}",
                )
            )
            continue
        try:
            link_target = path.resolve(strict=True)
            canonical_target = target.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            failures.append(
                Action(
                    "verify-fail",
                    rel,
                    f"compatibility link target cannot be resolved: {type(exc).__name__}",
                )
            )
            continue
        if link_target != canonical_target:
            failures.append(
                Action(
                    "verify-fail",
                    rel,
                    f"compatibility link does not target {target_rel}",
                )
            )
            continue
        valid_compatibility_paths.add(rel)
        valid_compatibility_links += 1

    expected: dict[str, set[str]] = {"": set()}
    for rel in rows:
        pure = PurePosixPath(rel)
        parent = "" if str(pure.parent) == "." else pure.parent.as_posix()
        expected.setdefault(parent, set()).add(pure.name)
    compatibility_parents: set[str] = set()
    for rel in sorted(valid_compatibility_paths):
        parent = ""
        for part in PurePosixPath(rel).parts:
            expected.setdefault(parent, set()).add(part)
            parent = part if not parent else f"{parent}/{part}"
            if parent != rel:
                compatibility_parents.add(parent)
    structural_parents = {
        rel for rel, row in rows.items() if row["kind"] == "structural"
    }
    max_scan_entries = int(data["limits"]["max_scan_entries"])
    scanned_entries = 0
    scan_exhausted = False
    for parent_rel, child_names in expected.items():
        if (
            parent_rel
            and parent_rel not in structural_parents
            and parent_rel not in compatibility_parents
        ):
            continue
        if parent_rel in unsafe:
            continue
        if not parent_rel:
            parent = root
        elif parent_rel in safe_paths:
            parent = safe_paths[parent_rel]
        else:
            try:
                parent = _safe_destination(root, parent_rel)
            except ContractError:
                continue
        if not parent.is_dir() or parent.is_symlink():
            continue
        scan_failures: list[Action] = []
        try:
            with os.scandir(parent) as entries:
                for child in entries:
                    if scanned_entries >= max_scan_entries:
                        scan_failures.append(
                            Action(
                                "verify-unmeasured",
                                parent_rel or ".",
                                "scan entry limit reached; Workspace parity is unmeasured",
                            )
                        )
                        scan_exhausted = True
                        break
                    scanned_entries += 1
                    if child.name not in child_names:
                        child_rel = (
                            child.name
                            if not parent_rel
                            else f"{parent_rel}/{child.name}"
                        )
                        scan_failures.append(
                            Action(
                                "verify-fail",
                                child_rel,
                                "undeclared structural entry",
                            )
                        )
        except OSError:
            failures.append(
                Action(
                    "verify-unmeasured",
                    parent_rel or ".",
                    "directory scan failed; Workspace parity is unmeasured",
                )
            )
        else:
            failures.extend(scan_failures)
        if scan_exhausted:
            break
    for rel, row in rows.items():
        if rel in unsafe or _blocked_ancestor(rel, {path: False for path in unsafe}):
            continue
        path = safe_paths[rel]
        if not path.exists():
            failures.append(Action("verify-fail", rel, "declared entry is absent"))
        elif row["kind"] in DIRECTORY_KINDS and (
            not path.is_dir() or path.is_symlink()
        ):
            failures.append(
                Action("verify-fail", rel, "declared directory is not physical")
            )
        elif row["kind"] == "private" and _private_mode(path) != 0o700:
            failures.append(
                Action("verify-fail", rel, "private container mode is not 0700")
            )
        elif row["kind"] == "index" and (not path.is_file() or path.is_symlink()):
            failures.append(
                Action("verify-fail", rel, "declared index is not a physical file")
            )
        elif row["kind"] == "repository" and not _repo_matches(path, row):
            failures.append(
                Action(
                    "verify-fail",
                    rel,
                    "repository remote or custody_ref does not match manifest",
                )
            )
    max_compatibility_links = int(data["limits"]["max_compatibility_links"])
    if valid_compatibility_links > max_compatibility_links:
        failures.append(
            Action(
                "verify-fail",
                ".",
                "present compatibility links exceed declared limit: "
                f"{valid_compatibility_links} > {max_compatibility_links}",
            )
        )
    return failures


def render(report: Mapping[str, Any]) -> str:
    lines = [
        f"jack: {report['mode']} {'OK' if report['ok'] else 'BLOCKED'}",
        f"  root: {report['workspace_root']}",
        (
            f"  actions={len(report['actions'])} applied={len(report['applied'])} "
            f"blockers={len(report['blockers'])} failures={len(report['failures'])}"
        ),
    ]
    for section in ("actions", "applied", "blockers", "failures"):
        for row in report[section]:
            lines.append(
                f"  [{section}:{row['operation']}] {row['path']}: {row['detail']}"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan", action="store_true", help="show the additive plan; change nothing"
    )
    mode.add_argument(
        "--verify", action="store_true", help="require exact final tree parity"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--receipt", type=Path, help="write the bounded JSON report")
    args = parser.parse_args()
    selected_mode = "verify" if args.verify else "plan" if args.plan else "apply"
    manifest = (
        args.manifest
        or Path(__file__).resolve().parents[1]
        / "governance"
        / "workspace-manifest.yaml"
    )

    applied: list[Action] = []
    actions: list[Action] = []
    blockers: list[Action] = []
    failures: list[Action] = []
    root: Path | None = None
    raw: bytes | None = None
    try:
        data, raw = load_manifest(manifest)
        root = resolve_root(data, args.root)
        actions, blockers = plan(data, root)
        if args.verify:
            failures = verify(data, root)
            actions = [action for action in actions if action.operation != "symlink"]
        elif not args.plan:
            applied = apply_actions(data, root, actions)
            actions, blockers = plan(data, root)
        ok = not blockers and not failures and (args.plan or not actions)
        report = {
            "schema": REPORT_SCHEMA,
            "mode": selected_mode,
            "ok": ok,
            "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "workspace_root": str(root),
            "actions": [row.as_dict() for row in actions],
            "applied": [row.as_dict() for row in applied],
            "blockers": [row.as_dict() for row in blockers],
            "failures": [row.as_dict() for row in failures],
        }
    except ApplyError as exc:
        report = {
            "schema": REPORT_SCHEMA,
            "mode": selected_mode,
            "ok": False,
            "manifest_sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "workspace_root": str(root) if root else None,
            "actions": [row.as_dict() for row in actions],
            "applied": [row.as_dict() for row in exc.applied],
            "blockers": [row.as_dict() for row in blockers],
            "failures": [row.as_dict() for row in failures],
            "error": str(exc),
            "failed_action": (
                exc.failed_action.as_dict() if exc.failed_action is not None else None
            ),
        }
    except ContractError as exc:
        report = {
            "schema": REPORT_SCHEMA,
            "mode": selected_mode,
            "ok": False,
            "error": str(exc),
        }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt_report = dict(report)
        if "workspace_root" in receipt_report:
            receipt_report["workspace_root"] = "$WORKSPACE_ROOT"
        rendered = json.dumps(receipt_report, indent=2, sort_keys=True) + "\n"
        if (
            not args.receipt.exists()
            or args.receipt.read_text(encoding="utf-8") != rendered
        ):
            args.receipt.write_text(rendered, encoding="utf-8")
    print(
        json.dumps(report, indent=2, sort_keys=True)
        if args.json
        else render(report)
        if "error" not in report
        else f"jack: ERROR\n  {report['error']}"
    )
    return 0 if report["ok"] or (args.plan and "error" not in report) else 1


if __name__ == "__main__":
    sys.exit(main())
