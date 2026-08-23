#!/usr/bin/env python3
"""Validate the lockfile-verified Markdownlint workflow and exception contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "markdownlint.yml"
CONFIG = ROOT / ".markdownlint-cli2.jsonc"
RUNNER = ROOT / "scripts" / "run-markdownlint.mjs"
TEST = ROOT / "tests" / "scripts" / "test-run-markdownlint.mjs"
PACKAGE = ROOT / "package.json"
LOCKFILE = ROOT / "package-lock.json"
QUALITY = ROOT / ".github" / "workflows" / "quality-gate.yml"


def require(text: str, needle: str, source: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{source}: missing {needle!r}")


def main() -> int:
    failures: list[str] = []
    for path in (WORKFLOW, CONFIG, RUNNER, TEST, PACKAGE, LOCKFILE, QUALITY):
        if not path.is_file():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
    if failures:
        print("markdownlint_workflow=failed")
        print("\n".join(failures))
        return 1

    workflow = WORKFLOW.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    quality = QUALITY.read_text(encoding="utf-8")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    lockfile = json.loads(LOCKFILE.read_text(encoding="utf-8"))

    version = "0.23.2"
    dependencies = package.get("devDependencies", {})
    locked = lockfile.get("packages", {}).get("", {}).get("devDependencies", {})
    if dependencies.get("markdownlint-cli2") != version:
        failures.append(f"package must pin markdownlint-cli2 exactly to {version}")
    if locked.get("markdownlint-cli2") != version:
        failures.append(f"lockfile root must pin markdownlint-cli2 exactly to {version}")

    expected_config = {
        "config": {"MD013": False},
        "overrides": [
            {
                "filter": [
                    ".github/PULL_REQUEST_TEMPLATE.md",
                    "tests/fixtures/LICENSES/heic2any-LICENSE.md",
                ],
                "config": {"MD041": False},
                "combine": "merge",
            }
        ],
    }
    if config != expected_config:
        failures.append("Markdownlint config must contain only the contracted exceptions")

    for needle in (
        "workflow_dispatch:",
        "pull_request:",
        "push:",
        "branches: [main]",
        "permissions:\n  contents: read",
        "timeout-minutes: 10",
        "node-version: 22.23.2",
        "npm ci --ignore-scripts",
        "node --test tests/scripts/test-run-markdownlint.mjs",
        "node scripts/run-markdownlint.mjs",
    ):
        require(workflow, needle, "Markdownlint workflow", failures)
    if re.search(r"^\s*(schedule|pull_request_target)\s*:", workflow, re.MULTILINE):
        failures.append("Markdownlint workflow: unexpected privileged/noisy trigger")
    if re.search(r"^\s*[\w-]+:\s*write\s*$", workflow, re.MULTILINE):
        failures.append("Markdownlint workflow: write permission is forbidden")

    action_refs = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
    expected_refs = [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
    ]
    if action_refs != expected_refs:
        failures.append(f"Markdownlint workflow: unexpected Action inventory: {action_refs}")

    for needle in (
        "['ls-files', '-z', '--', '*.md']",
        "tracked Markdown inventory is empty",
        ".markdownlint-cli2.jsonc",
    ):
        require(runner, needle, "Markdownlint runner", failures)
    for test_name in (
        "tracked inventory excludes untracked and non-Markdown files",
        "empty inventory fails closed",
        "discovery failure is propagated",
        "unsafe inventory path is rejected",
        "invocation uses the exact config and complete inventory",
    ):
        require(tests, test_name, "Markdownlint tests", failures)
    for command in (
        "node --test tests/scripts/test-run-markdownlint.mjs",
        "./scripts/check-markdownlint-workflow.py",
    ):
        require(quality, command, "quality gate", failures)

    if failures:
        print("markdownlint_workflow=failed")
        print("\n".join(failures))
        return 1
    print(
        "markdownlint_workflow=passed "
        "version=0.23.2 tests=5 exceptions=MD013+2xMD041 action_references=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
