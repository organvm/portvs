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
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any, Mapping
from urllib.parse import urlparse

import yaml


SCHEMA = "portvs.workspace_manifest.v1"
REPORT_SCHEMA = "portvs.workspace_bootstrap_report.v1"
KINDS = {"structural", "repository", "private", "ephemeral", "index"}
DIRECTORY_KINDS = {"structural", "repository", "private", "ephemeral"}


class ContractError(ValueError):
    pass


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


def load_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    if not path.is_file():
        raise ContractError(f"manifest missing: {path}")
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
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ContractError(f"rows[{index}] must be a mapping")
        for field in ("path", "kind", "owner_ref", "residency"):
            if not row.get(field):
                raise ContractError(f"rows[{index}] is missing {field}")
        rel = _safe_path(row["path"])
        if rel in seen:
            raise ContractError(f"duplicate manifest path: {rel}")
        seen.add(rel)
        if row["kind"] not in KINDS:
            raise ContractError(f"{rel}: unsupported kind {row['kind']!r}")
        for legacy in row.get("legacy_paths") or []:
            _safe_path(legacy)
    migration = data.get("migration") or {}
    if not isinstance(migration, dict):
        raise ContractError("migration must be a mapping")
    links = migration.get("compatibility_links") or []
    if not isinstance(links, list):
        raise ContractError("migration.compatibility_links must be a list")
    for row in links:
        if not isinstance(row, dict):
            raise ContractError("compatibility link rows must be mappings")
        for field in ("path", "target", "owner_ref", "expires_at"):
            if not row.get(field):
                raise ContractError(f"compatibility link is missing {field}")
        _safe_path(row["path"])
        _safe_path(row["target"])
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
    return root.resolve(strict=False)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_destination(root: Path, rel: str) -> Path:
    candidate = root / rel
    cursor = root
    for part in PurePosixPath(rel).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            target = cursor.resolve(strict=False)
            if not _inside(target, root):
                raise ContractError(
                    f"{rel}: symlink component escapes Workspace: {cursor}"
                )
            raise ContractError(
                f"{rel}: canonical entries cannot traverse a symlink: {cursor}"
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
    return proc.returncode == 0 and _canonical_remote(
        proc.stdout.strip()
    ) == _canonical_remote(str(row["remote"]))


def plan(data: Mapping[str, Any], root: Path) -> tuple[list[Action], list[Action]]:
    actions: list[Action] = []
    blockers: list[Action] = []
    rows = sorted(
        data["rows"],
        key=lambda row: (len(PurePosixPath(row["path"]).parts), row["path"]),
    )
    for row in rows:
        rel = _safe_path(row["path"])
        try:
            path = _safe_destination(root, rel)
        except ContractError as exc:
            blockers.append(Action("blocked", rel, str(exc)))
            continue
        kind = row["kind"]
        if kind in {"structural", "private", "ephemeral"}:
            if path.exists():
                if not path.is_dir() or path.is_symlink():
                    blockers.append(
                        Action("blocked", rel, f"{kind} requires a physical directory")
                    )
            else:
                actions.append(
                    Action("mkdir", rel, f"create declared {kind} container")
                )
        elif kind == "index":
            desired = _index_bytes(row)
            if path.exists():
                if not path.is_file() or path.is_symlink():
                    blockers.append(
                        Action("blocked", rel, "index path is not a physical file")
                    )
                elif path.read_bytes() != desired:
                    blockers.append(
                        Action(
                            "blocked",
                            rel,
                            "existing index differs; bootstrap never overwrites",
                        )
                    )
            else:
                actions.append(Action("write-index", rel, str(row["source_ref"])))
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
            else:
                actions.append(Action("clone", rel, str(row["remote"])))

    migration = data.get("migration") or {}
    for row in migration.get("compatibility_links") or []:
        rel = _safe_path(row["path"])
        target_rel = _safe_path(row["target"])
        path = root / rel
        target = root / target_rel
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
        elif target.exists():
            actions.append(Action("symlink", rel, target_rel))
        else:
            blockers.append(
                Action("blocked", rel, f"compatibility target is absent: {target_rel}")
            )
    return actions, blockers


def _row_by_path(data: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(row["path"]): row for row in data["rows"]}


def apply_actions(
    data: Mapping[str, Any], root: Path, actions: list[Action]
) -> list[Action]:
    applied: list[Action] = []
    rows = _row_by_path(data)
    if not root.exists():
        root.mkdir(parents=True)
        applied.append(Action("mkdir-root", ".", "create Workspace root"))
    elif not root.is_dir() or root.is_symlink():
        raise ContractError("Workspace root must be a physical directory")

    for action in actions:
        path = _safe_destination(root, action.path)
        if action.operation == "mkdir":
            path.mkdir()
        elif action.operation == "write-index":
            path.write_bytes(_index_bytes(rows[action.path]))
        elif action.operation == "clone":
            row = rows[action.path]
            command = ["git", "clone", "--origin", "origin"]
            if branch := row.get("default_branch"):
                command.extend(["--branch", str(branch), "--single-branch"])
            command.extend([str(row["remote"]), str(path)])
            proc = subprocess.run(command, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise ContractError(
                    f"{action.path}: clone failed: {proc.stderr.strip()[:500]}"
                )
        elif action.operation == "symlink":
            target = root / action.detail
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(target, target_is_directory=True)
        else:
            raise ContractError(f"unsupported action: {action.operation}")
        applied.append(action)
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
    expected: dict[str, set[str]] = {"": set()}
    for rel in rows:
        pure = PurePosixPath(rel)
        parent = "" if str(pure.parent) == "." else pure.parent.as_posix()
        expected.setdefault(parent, set()).add(pure.name)
    for parent_rel, child_names in expected.items():
        if parent_rel and rows[parent_rel]["kind"] != "structural":
            continue
        parent = root if not parent_rel else root / parent_rel
        if not parent.is_dir() or parent.is_symlink():
            continue
        for child in parent.iterdir():
            if child.name not in child_names:
                failures.append(
                    Action(
                        "verify-fail",
                        child.relative_to(root).as_posix(),
                        "undeclared structural entry",
                    )
                )
    for rel, row in rows.items():
        path = root / rel
        if not path.exists():
            failures.append(Action("verify-fail", rel, "declared entry is absent"))
        elif row["kind"] in DIRECTORY_KINDS and (
            not path.is_dir() or path.is_symlink()
        ):
            failures.append(
                Action("verify-fail", rel, "declared directory is not physical")
            )
        elif row["kind"] == "index" and (not path.is_file() or path.is_symlink()):
            failures.append(
                Action("verify-fail", rel, "declared index is not a physical file")
            )
        elif row["kind"] == "repository" and not _repo_matches(path, row):
            failures.append(
                Action("verify-fail", rel, "repository remote does not match manifest")
            )
    links = (data.get("migration") or {}).get("compatibility_links") or []
    if links:
        for row in links:
            failures.append(
                Action(
                    "verify-fail",
                    str(row["path"]),
                    "unresolved migration row; final convergence requires zero compatibility links",
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
    manifest = (
        args.manifest
        or Path(__file__).resolve().parents[1]
        / "governance"
        / "workspace-manifest.yaml"
    )

    try:
        data, raw = load_manifest(manifest)
        root = resolve_root(data, args.root)
        actions, blockers = plan(data, root)
        applied: list[Action] = []
        failures: list[Action] = []
        selected_mode = "verify" if args.verify else "plan" if args.plan else "apply"
        if args.verify:
            failures = verify(data, root)
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
    except ContractError as exc:
        report = {
            "schema": REPORT_SCHEMA,
            "mode": "error",
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
