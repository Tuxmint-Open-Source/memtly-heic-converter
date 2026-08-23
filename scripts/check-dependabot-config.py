#!/usr/bin/env python3
"""Validate the intended low-noise Dependabot configuration contract."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".github" / "dependabot.yml"


def require(text: str, needle: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"missing required Dependabot config: {needle}")


def main() -> int:
    failures: list[str] = []
    if not CONFIG.is_file():
        print("dependabot_config=failed")
        print("missing file: .github/dependabot.yml")
        return 1

    text = CONFIG.read_text(encoding="utf-8")
    if "\t" in text:
        failures.append("tab characters are not allowed")

    required = [
        "version: 2",
        "package-ecosystem: npm",
        "package-ecosystem: github-actions",
        "directory: /",
        "interval: weekly",
        "day: monday",
        "timezone: Etc/UTC",
        "open-pull-requests-limit: 3",
        '"type: chore"',
        "npm-development:",
        "dependency-type: development",
        "github-actions:",
        'patterns:\n          - "*"',
    ]
    for needle in required:
        require(text, needle, failures)

    exact_counts = {
        "package-ecosystem:": 2,
        "directory: /": 2,
        "interval: weekly": 2,
        "day: monday": 2,
        "timezone: Etc/UTC": 2,
        "open-pull-requests-limit: 3": 2,
        '"type: chore"': 2,
    }
    for needle, expected in exact_counts.items():
        actual = text.count(needle)
        if actual != expected:
            failures.append(
                f"unexpected count for {needle!r}: expected {expected}, got {actual}"
            )

    forbidden = [
        "package-ecosystem: docker",
        "package-ecosystem: pip",
        "target-branch:",
        "registries:",
        "insecure-external-code-execution:",
    ]
    for needle in forbidden:
        if needle in text:
            failures.append(f"unexpected Dependabot config: {needle}")

    if failures:
        print("dependabot_config=failed")
        print("\n".join(failures))
        return 1

    print("dependabot_config=passed ecosystems=2 grouped=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
