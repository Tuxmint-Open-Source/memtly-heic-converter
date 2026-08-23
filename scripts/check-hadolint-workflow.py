#!/usr/bin/env python3
"""Validate the verified hadolint workflow and Dockerfile contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "hadolint.yml"
RUNNER = ROOT / "scripts" / "run-hadolint.py"
TEST = ROOT / "tests" / "scripts" / "test-run-hadolint.py"
CONFIG = ROOT / ".hadolint.yaml"
DOCKERFILE = ROOT / "Dockerfile"
QUALITY = ROOT / ".github" / "workflows" / "quality-gate.yml"


def require(text: str, needle: str, source: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{source}: missing {needle!r}")


def main() -> int:
    failures: list[str] = []
    for path in (WORKFLOW, RUNNER, TEST, CONFIG, DOCKERFILE, QUALITY):
        if not path.is_file():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
    if failures:
        print("hadolint_workflow=failed")
        print("\n".join(failures))
        return 1

    workflow = WORKFLOW.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    quality = QUALITY.read_text(encoding="utf-8")

    for needle in (
        "workflow_dispatch:",
        "pull_request:",
        "push:",
        "branches: [main]",
        "permissions:\n  contents: read",
        "timeout-minutes: 10",
        "python3 tests/scripts/test-run-hadolint.py",
        "python3 scripts/run-hadolint.py",
    ):
        require(workflow, needle, "hadolint workflow", failures)
    if re.search(r"^\s*(schedule|pull_request_target)\s*:", workflow, re.MULTILINE):
        failures.append("hadolint workflow: unexpected privileged/noisy trigger")
    if re.search(r"^\s*[\w-]+:\s*write\s*$", workflow, re.MULTILINE):
        failures.append("hadolint workflow: write permission is forbidden")

    action_refs = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
    if action_refs != [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    ]:
        failures.append(f"hadolint workflow: unexpected Action inventory: {action_refs}")

    for needle in (
        'VERSION = "2.15.1"',
        'BINARY_SHA256 = "c7187db94eeeeca956519a6af171adc31453941a1e777961f6e680f697c8c507"',
        '":(glob)**/Dockerfile.*"',
        '"--failure-threshold"',
        '"style"',
        "if actual_sha256 != expected_sha256:",
    ):
        require(runner, needle, "hadolint runner", failures)

    expected_config = (
        "# Separate test, restore, build, publish, and artifact-verification layers are\n"
        "# intentional cache and review boundaries in this reproducible overlay build.\n"
        "ignored:\n"
        "  - DL3059\n"
    )
    if config != expected_config:
        failures.append("hadolint config must contain only the documented DL3059 exception")

    for forbidden in ("| awk", "npm --version |", "cd /src;"):
        if forbidden in dockerfile:
            failures.append(f"Dockerfile retains remediated pattern: {forbidden}")
    for required in (
        "WORKDIR /src\nRUN set -eux;",
        "git ls-tree --format='%(objectname)' HEAD Memtly.Core",
        'npm_major="${npm_version%%.*}"',
    ):
        require(dockerfile, required, "Dockerfile remediation", failures)

    for test_name in (
        "test_verified_download_installs_exact_binary",
        "test_checksum_failure_stops_before_installation",
        "test_tracked_inventory_includes_nested_variants_only",
        "test_invocation_uses_exact_config_threshold_and_inventory",
    ):
        require(tests, test_name, "hadolint tests", failures)

    for command in (
        "python3 tests/scripts/test-run-hadolint.py",
        "./scripts/check-hadolint-workflow.py",
    ):
        require(quality, command, "quality gate", failures)

    if failures:
        print("hadolint_workflow=failed")
        print("\n".join(failures))
        return 1

    print("hadolint_workflow=passed version=2.15.1 tests=4 ignored=DL3059")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
