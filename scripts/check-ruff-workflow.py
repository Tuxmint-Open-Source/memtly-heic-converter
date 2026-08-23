#!/usr/bin/env python3
"""Validate the verified Ruff workflow and acquisition contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "ruff.yml"
RUNNER = ROOT / "scripts" / "run-ruff.py"
TEST = ROOT / "tests" / "scripts" / "test-run-ruff.py"
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
        print("ruff_workflow=failed")
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
        "python3 tests/scripts/test-run-ruff.py",
        "python3 scripts/run-ruff.py",
    ):
        require(workflow, needle, "Ruff workflow", failures)

    if re.search(r"^\s*(schedule|pull_request_target)\s*:", workflow, re.MULTILINE):
        failures.append("Ruff workflow: unexpected privileged/noisy trigger")
    if re.search(r"^\s*[\w-]+:\s*write\s*$", workflow, re.MULTILINE):
        failures.append("Ruff workflow: write permission is forbidden")

    action_refs = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
    if action_refs != [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    ]:
        failures.append(f"Ruff workflow: unexpected Action inventory: {action_refs}")

    for needle in (
        'VERSION = "0.16.4"',
        'ARCHIVE_NAME = "ruff-x86_64-unknown-linux-gnu.tar.gz"',
        'ARCHIVE_SHA256 = "9cb1234804ddb0f7f57cef3f81623ce5acb990e40af7cce08dc7778c9d7ee96c"',
        'RULES = "E4,E7,E9,F,I,EXE,B,UP"',
        '["git", "ls-files", "-z", "--", "*.py"]',
        '"--no-cache"',
        '"--output-format=concise"',
        "if actual_sha256 != expected_sha256:",
        "if names != {ARCHIVE_DIRECTORY, ARCHIVE_BINARY}:",
        "if not directory.isdir() or not binary.isfile():",
    ):
        require(runner, needle, "Ruff runner", failures)

    for test_name in (
        "test_verified_archive_installs_exact_binary",
        "test_checksum_failure_stops_before_archive_parsing",
        "test_unsafe_or_unexpected_archive_inventory_is_rejected",
        "test_tracked_python_inventory_excludes_untracked_files",
        "test_invocation_pins_rules_output_and_cache_behavior",
    ):
        require(tests, test_name, "Ruff tests", failures)

    for command in (
        "python3 tests/scripts/test-run-ruff.py",
        "./scripts/check-ruff-workflow.py",
    ):
        require(quality, command, "quality gate", failures)

    if failures:
        print("ruff_workflow=failed")
        print("\n".join(failures))
        return 1

    print("ruff_workflow=passed version=0.16.4 tests=5 action_references=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
