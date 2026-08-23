"""Check public upstream drift for the pinned Memtly patch surface.

The checker compares the committed baseline with public upstream Git refs and
watched file hashes. Drift means "review needed", not "compatible".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / ".upstream" / "memtly.lock.json"
REPORT_PATH = ROOT / ".upstream" / "memtly-drift-report.md"
VERSIONS_PATH = ROOT / "config" / "versions.env"


def run(args: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def load_versions() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in VERSIONS_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.lstrip().startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key] = value
    return values


def load_baseline() -> dict[str, Any]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def remote_head(repo: str) -> tuple[str, str]:
    output = run(["git", "ls-remote", "--symref", repo, "HEAD"])
    branch = ""
    commit = ""
    for line in output.splitlines():
        if line.startswith("ref:"):
            branch = line.split()[1].removeprefix("refs/heads/")
        elif line.endswith("\tHEAD"):
            commit = line.split()[0]
    return branch, commit


def latest_semverish_tag(repo: str) -> str:
    output = run(["git", "ls-remote", "--tags", "--sort=version:refname", repo, "refs/tags/*"])
    latest = ""
    for line in output.splitlines():
        ref = line.split("\t", 1)[1]
        if ref.endswith("^{}"):
            continue
        latest = ref.removeprefix("refs/tags/")
    return latest


def clone_at(repo: str, commit: str, dest: Path) -> None:
    run(["git", "clone", "--filter=blob:none", "--no-checkout", repo, str(dest)])
    run(["git", "checkout", "--detach", commit], cwd=dest)


def sha256_file(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def git_blob_oid(repo: Path, path: str, commit: str = "HEAD") -> str:
    if path == "Memtly.Core":
        output = run(["git", "ls-tree", commit, path], cwd=repo)
        return output.split()[2]
    return run(["git", "rev-parse", f"{commit}:{path}"], cwd=repo)


def current_snapshot(tmpdir: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    upstreams = baseline["upstreams"]
    community_repo = upstreams["community"]["repo"]
    core_repo = upstreams["core"]["repo"]
    community_commit = upstreams["community"]["commit"]
    core_commit = upstreams["core"]["commit"]

    community_path = tmpdir / "community"
    core_path = tmpdir / "core"
    clone_at(community_repo, community_commit, community_path)
    clone_at(core_repo, core_commit, core_path)

    community_branch, community_head = remote_head(community_repo)
    core_branch, core_head = remote_head(core_repo)
    latest_tag = latest_semverish_tag(community_repo)

    files: list[dict[str, Any]] = []
    for entry in baseline["watched_files"]:
        repo_name = entry["repo"]
        rel = entry["path"]
        if repo_name == "community":
            files.append({
                "repo": repo_name,
                "path": rel,
                "git_object": "gitlink",
                "git_oid": git_blob_oid(community_path, rel),
            })
            continue
        sha, size = sha256_file(core_path / rel)
        files.append({
            "repo": repo_name,
            "path": rel,
            "git_object": "blob",
            "git_oid": git_blob_oid(core_path, rel),
            "sha256": sha,
            "bytes": size,
        })

    return {
        "schema": baseline.get("schema", 1),
        "description": baseline.get("description", "Public-safe upstream drift baseline."),
        "upstreams": {
            "community": {
                "repo": community_repo,
                "tag": upstreams["community"]["tag"],
                "tag_object": upstreams["community"].get("tag_object", ""),
                "commit": community_commit,
                "default_branch": community_branch,
                "observed_default_branch_head": community_head,
                "observed_latest_tag": latest_tag,
            },
            "core": {
                "repo": core_repo,
                "commit": core_commit,
                "default_branch": core_branch,
                "observed_default_branch_head": core_head,
            },
        },
        "watched_files": files,
    }


def public_diff_summary(old: dict[str, Any], new: dict[str, Any]) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    changed: list[str] = []

    old_up = old["upstreams"]
    new_up = new["upstreams"]
    for name in ("community", "core"):
        for field in ("observed_default_branch_head", "observed_latest_tag"):
            if field not in old_up[name] and field not in new_up[name]:
                continue
            old_value = old_up[name].get(field, "")
            new_value = new_up[name].get(field, "")
            if old_value != new_value:
                changed.append(f"{name}.{field}")
                lines.append(f"- `{name}.{field}` changed from `{old_value}` to `{new_value}`.")

    old_files = {(item["repo"], item["path"]): item for item in old["watched_files"]}
    new_files = {(item["repo"], item["path"]): item for item in new["watched_files"]}
    for key in sorted(set(old_files) | set(new_files)):
        old_item = old_files.get(key)
        new_item = new_files.get(key)
        label = f"{key[0]}:{key[1]}"
        if old_item is None:
            changed.append(label)
            lines.append(f"- `{label}` was added to the watched baseline.")
        elif new_item is None:
            changed.append(label)
            lines.append(f"- `{label}` was removed from the watched baseline.")
        elif old_item != new_item:
            changed.append(label)
            lines.append(f"- `{label}` hash/object changed.")
    return changed, lines


def write_report(old: dict[str, Any], new: dict[str, Any], changes: list[str], lines: list[str]) -> None:
    community = new["upstreams"]["community"]
    core = new["upstreams"]["core"]
    body = [
        "# Upstream Memtly drift review",
        "",
        "This report is public-safe and contains public upstream Git metadata only.",
        "A drift report is a review prompt, not a compatibility claim.",
        "",
        "## Pinned compatibility inputs",
        "",
        f"- Memtly Community tag: `{community['tag']}`",
        f"- Memtly Community commit: `{community['commit']}`",
        f"- Memtly Core commit: `{core['commit']}`",
        "",
        "## Observed upstream state",
        "",
        f"- Community default branch `{community['default_branch']}`: `{community['observed_default_branch_head']}`",
        f"- Community latest tag: `{community['observed_latest_tag']}`",
        f"- Core default branch `{core['default_branch']}`: `{core['observed_default_branch_head']}`",
        "",
        "## Drift summary",
        "",
    ]
    body.extend(lines or ["- No drift detected."])
    body.extend([
        "",
        "## Review checklist",
        "",
        "- [ ] Decide whether upstream changes affect the overlay patch surface.",
        "- [ ] If a new Memtly release is targeted, validate the exact release/artifact before changing compatibility claims.",
        "- [ ] Keep raw runtime evidence and environment-specific validation details out of public artifacts.",
        "",
        "## Local validation",
        "",
        "```sh",
        "python3 scripts/check-upstream-drift.py --check",
        "```",
        "",
    ])
    REPORT_PATH.write_text("\n".join(body), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit non-zero when drift is detected")
    parser.add_argument("--write", action="store_true", help="write updated baseline and drift report")
    args = parser.parse_args()
    if args.check == args.write:
        parser.error("choose exactly one of --check or --write")

    baseline = load_baseline()
    versions = load_versions()
    if versions.get("MEMTLY_COMMUNITY_COMMIT") != baseline["upstreams"]["community"]["commit"]:
        raise SystemExit("config/versions.env MEMTLY_COMMUNITY_COMMIT differs from baseline")
    if versions.get("MEMTLY_CORE_COMMIT") != baseline["upstreams"]["core"]["commit"]:
        raise SystemExit("config/versions.env MEMTLY_CORE_COMMIT differs from baseline")

    with tempfile.TemporaryDirectory(prefix="memtly-upstream-drift-") as tmp:
        current = current_snapshot(Path(tmp), baseline)

    changes, lines = public_diff_summary(baseline, current)
    if args.write:
        if changes:
            BASELINE_PATH.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_report(baseline, current, changes, lines)

    if changes:
        print("upstream_drift=detected")
        for line in lines:
            print(line)
        return 1 if args.check else 0

    print("upstream_drift=none")
    if args.write:
        write_report(baseline, current, changes, lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
