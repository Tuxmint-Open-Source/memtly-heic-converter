#!/usr/bin/env python3
"""Validate the explicit CodeQL workflow contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "codeql.yml"
QUALITY_GATE = ROOT / ".github" / "workflows" / "quality-gate.yml"

REQUIRED_TEXT = [
    "name: Code scanning",
    "workflow_dispatch:",
    "pull_request:",
    "push:",
    "branches: [main]",
    "schedule:",
    "cron: '17 4 * * 2'",
    "contents: read",
    "security-events: write",
    "fail-fast: false",
    "- actions",
    "- javascript-typescript",
    "- python",
    "languages: ${{ matrix.language }}",
    "category: /language:${{ matrix.language }}",
]

REQUIRED_REFS = {
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "github/codeql-action/init@db488ddef3bf6cb639b32c2e9a7c0a7ea8271d28",
    "github/codeql-action/analyze@db488ddef3bf6cb639b32c2e9a7c0a7ea8271d28",
}
USES_PATTERN = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
WRITE_PERMISSION = re.compile(r"^\s*([a-z-]+):\s*write\s*$", re.MULTILINE)


def main() -> int:
    failures: list[str] = []
    if not WORKFLOW.is_file():
        print("codeql_workflow=failed")
        print("missing .github/workflows/codeql.yml")
        return 1

    text = WORKFLOW.read_text(encoding="utf-8")
    for needle in REQUIRED_TEXT:
        if needle not in text:
            failures.append(f"missing CodeQL workflow contract text: {needle}")

    if "pull_request_target:" in text:
        failures.append("pull_request_target is forbidden for CodeQL scanning")
    concurrency_block = text.split("jobs:", 1)[0]
    if "matrix." in concurrency_block:
        failures.append("workflow-level configuration cannot reference the job matrix")
    if re.search(r"^\s*queries\s*:", text, re.MULTILINE):
        failures.append("CodeQL must use its default query suite; remove queries override")
    if "autobuild@" in text:
        failures.append("autobuild is unnecessary for the interpreted repository languages")

    references = set(USES_PATTERN.findall(text))
    if references != REQUIRED_REFS:
        failures.append(
            "unexpected CodeQL Action inventory: "
            + ", ".join(sorted(references))
        )

    write_permissions = set(WRITE_PERMISSION.findall(text))
    if write_permissions != {"security-events"}:
        failures.append(
            "security-events must be the only write permission: "
            + ", ".join(sorted(write_permissions))
        )

    quality_text = QUALITY_GATE.read_text(encoding="utf-8")
    if "./scripts/check-codeql-workflow.py" not in quality_text:
        failures.append("required quality gate does not run CodeQL workflow contract")

    if failures:
        print("codeql_workflow=failed")
        print("\n".join(failures))
        return 1

    print(
        "codeql_workflow=passed "
        f"languages=3 action_references={len(references)} write_permissions=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
