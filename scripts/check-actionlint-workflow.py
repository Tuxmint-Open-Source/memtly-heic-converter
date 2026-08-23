#!/usr/bin/env python3
"""Validate the verified actionlint workflow and acquisition contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "actionlint.yml"
RUNNER = ROOT / "scripts" / "run-actionlint.py"
TEST = ROOT / "tests" / "scripts" / "test-run-actionlint.py"
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
        print("actionlint_workflow=failed")
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
        "python3 tests/scripts/test-run-actionlint.py",
        "python3 scripts/run-actionlint.py",
    ):
        require(workflow, needle, "actionlint workflow", failures)

    if re.search(r"^\s*(schedule|pull_request_target)\s*:", workflow, re.MULTILINE):
        failures.append("actionlint workflow: unexpected privileged/noisy trigger")
    if re.search(r"^\s*[\w-]+:\s*write\s*$", workflow, re.MULTILINE):
        failures.append("actionlint workflow: write permission is forbidden")

    action_refs = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
    if action_refs != [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    ]:
        failures.append(f"actionlint workflow: unexpected Action inventory: {action_refs}")

    runner_contract = (
        'VERSION = "1.7.12"',
        'ARCHIVE_SHA256 = "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"',
        '".github/workflows/*.yml"',
        '".github/workflows/*.yaml"',
        '"-no-color"',
        '"-shellcheck="',
        '"-pyflakes="',
        "if actual_sha256 != expected_sha256:",
        "if names != ARCHIVE_MEMBERS:",
    )
    for needle in runner_contract:
        require(runner, needle, "actionlint runner", failures)

    for test_name in (
        "test_verified_archive_installs_exact_binary",
        "test_checksum_failure_stops_before_archive_parsing",
        "test_unsafe_or_unexpected_archive_inventory_is_rejected",
        "test_tracked_workflow_inventory_excludes_untracked_and_other_yaml",
        "test_invocation_disables_color_and_optional_external_linters",
    ):
        require(tests, test_name, "actionlint tests", failures)

    for command in (
        "python3 tests/scripts/test-run-actionlint.py",
        "./scripts/check-actionlint-workflow.py",
    ):
        require(quality, command, "quality gate", failures)

    if failures:
        print("actionlint_workflow=failed")
        print("\n".join(failures))
        return 1

    print("actionlint_workflow=passed version=1.7.12 tests=5 action_references=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
