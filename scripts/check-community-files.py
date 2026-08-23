#!/usr/bin/env python3
"""Validate required community health files and public-safety language."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_TEXT = {
    "CODE_OF_CONDUCT.md": [
        "Contributor Covenant Code of Conduct",
        "Do not use a public issue for a conduct report",
        "version 2.1",
    ],
    "CONTRIBUTING.md": [
        "Keep pull requests focused",
        "private environment data or personal photos",
        "Quality gates",
    ],
    "SECURITY.md": [
        "do not open a public issue",
        "private vulnerability reporting",
    ],
    ".github/PULL_REQUEST_TEMPLATE.md": [
        "Project quality gate",
        "Public-safety and scope",
        "private vulnerability reporting",
        "real hardware or emulation",
    ],
    ".github/ISSUE_TEMPLATE/bug_report.yml": [
        "name: Bug report",
        "exact commit tested",
        "real hardware from emulation",
        "Public-safety confirmation",
        "private vulnerability reporting",
    ],
    ".github/ISSUE_TEMPLATE/feature_request.yml": [
        "name: Feature request",
        "Compatibility and safety impact",
        "Public-safety confirmation",
    ],
    ".github/ISSUE_TEMPLATE/documentation.yml": [
        "name: Documentation improvement",
        "Public-safety confirmation",
    ],
    ".github/ISSUE_TEMPLATE/config.yml": [
        "blank_issues_enabled: false",
        "/security/advisories/new",
        "/issues/7",
    ],
}


def main() -> int:
    failures: list[str] = []
    for relative, needles in REQUIRED_TEXT.items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        if "\t" in text:
            failures.append(f"tab character is not allowed: {relative}")
        for needle in needles:
            if needle.lower() not in text.lower():
                failures.append(f"missing required text in {relative}: {needle}")

    if failures:
        print("community_files=failed")
        print("\n".join(failures))
        return 1

    print(f"community_files=passed files={len(REQUIRED_TEXT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
