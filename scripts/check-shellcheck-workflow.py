#!/usr/bin/env python3
"""Validate the verified ShellCheck workflow and acquisition contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "shellcheck.yml"
RUNNER = ROOT / "scripts" / "run-shellcheck.py"
TEST = ROOT / "tests" / "scripts" / "test-run-shellcheck.py"
QUALITY = ROOT / ".github" / "workflows" / "quality-gate.yml"


def require(text: str, needle: str, source: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{source}: missing {needle!r}")


def main() -> int:
    failures: list[str] = []
    for path in (WORKFLOW, RUNNER, TEST, QUALITY):
        if not path.is_file():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
    if failures:
        print("shellcheck_workflow=failed")
        print("\n".join(failures))
        return 1

    workflow = WORKFLOW.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    quality = QUALITY.read_text(encoding="utf-8")

    for needle in (
        "workflow_dispatch:",
        "pull_request:",
        "push:",
        "branches: [main]",
        "permissions:\n  contents: read",
        "timeout-minutes: 10",
        "python3 tests/scripts/test-run-shellcheck.py",
        "python3 scripts/run-shellcheck.py",
    ):
        require(workflow, needle, "shellcheck workflow", failures)

    if re.search(r"^\s*(schedule|pull_request_target)\s*:", workflow, re.MULTILINE):
        failures.append("shellcheck workflow: unexpected privileged/noisy trigger")
    if re.search(r"^\s*[\w-]+:\s*write\s*$", workflow, re.MULTILINE):
        failures.append("shellcheck workflow: write permission is forbidden")

    action_refs = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
    if action_refs != [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    ]:
        failures.append(f"shellcheck workflow: unexpected Action inventory: {action_refs}")

    runner_contract = (
        'VERSION = "0.11.0"',
        'ARCHIVE_SHA256 = "8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198"',
        '"git", "ls-files", "-z", "--", "*.sh", "*.bash"',
        '"--severity=style"',
        "if actual_sha256 != expected_sha256:",
        "if names != ARCHIVE_MEMBERS:",
    )
    for needle in runner_contract:
        require(runner, needle, "ShellCheck runner", failures)

    for test_name in (
        "test_verified_archive_installs_exact_binary",
        "test_checksum_failure_stops_before_archive_parsing",
        "test_unsafe_or_unexpected_archive_inventory_is_rejected",
        "test_tracked_inventory_comes_from_git_and_ignores_untracked_files",
    ):
        require(tests, test_name, "ShellCheck tests", failures)

    for command in (
        "python3 tests/scripts/test-run-shellcheck.py",
        "./scripts/check-shellcheck-workflow.py",
    ):
        require(quality, command, "quality gate", failures)

    if failures:
        print("shellcheck_workflow=failed")
        print("\n".join(failures))
        return 1

    print("shellcheck_workflow=passed version=0.11.0 tests=4 action_references=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
