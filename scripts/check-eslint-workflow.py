#!/usr/bin/env python3
"""Validate the lockfile-verified ESLint workflow and inventory contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "eslint.yml"
CONFIG = ROOT / "eslint.config.mjs"
RUNNER = ROOT / "scripts" / "run-eslint.mjs"
TEST = ROOT / "tests" / "scripts" / "test-run-eslint.mjs"
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
        print("eslint_workflow=failed")
        print("\n".join(failures))
        return 1

    workflow = WORKFLOW.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    quality = QUALITY.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    lockfile = json.loads(LOCKFILE.read_text(encoding="utf-8"))

    expected = {
        "@eslint/js": "10.0.1",
        "eslint": "10.9.0",
        "globals": "17.11.0",
    }
    dependencies = package.get("devDependencies", {})
    locked = lockfile.get("packages", {}).get("", {}).get("devDependencies", {})
    for name, version in expected.items():
        if dependencies.get(name) != version or locked.get(name) != version:
            failures.append(f"package/lockfile must pin {name} exactly to {version}")

    for needle in (
        "workflow_dispatch:",
        "pull_request:",
        "push:",
        "branches: [main]",
        "permissions:\n  contents: read",
        "timeout-minutes: 10",
        "node-version: 22.23.2",
        "npm ci --ignore-scripts",
        "node --test tests/scripts/test-run-eslint.mjs",
        "node scripts/run-eslint.mjs",
    ):
        require(workflow, needle, "ESLint workflow", failures)
    if re.search(r"^\s*(schedule|pull_request_target)\s*:", workflow, re.MULTILINE):
        failures.append("ESLint workflow: unexpected privileged/noisy trigger")
    if re.search(r"^\s*[\w-]+:\s*write\s*$", workflow, re.MULTILINE):
        failures.append("ESLint workflow: write permission is forbidden")

    action_refs = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
    expected_refs = [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
    ]
    if action_refs != expected_refs:
        failures.append(f"ESLint workflow: unexpected Action inventory: {action_refs}")

    for needle in (
        "js.configs.recommended.rules",
        "globals: globals.node",
        "...globals.browser",
    ):
        require(config, needle, "ESLint config", failures)
    for needle in (
        "['ls-files', '-z', '--', '*.js', '*.mjs', '*.cjs']",
        "tracked JavaScript inventory is empty",
        "--no-cache",
        "stylish",
    ):
        require(runner, needle, "ESLint runner", failures)
    for test_name in (
        "tracked inventory excludes untracked and non-JavaScript files",
        "empty inventory fails closed",
        "discovery failure is propagated",
        "unsafe inventory path is rejected",
        "invocation is cache-free and uses the complete inventory",
    ):
        require(tests, test_name, "ESLint tests", failures)
    for command in (
        "node --test tests/scripts/test-run-eslint.mjs",
        "./scripts/check-eslint-workflow.py",
    ):
        require(quality, command, "quality gate", failures)

    if failures:
        print("eslint_workflow=failed")
        print("\n".join(failures))
        return 1
    print("eslint_workflow=passed version=10.9.0 tests=5 action_references=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
