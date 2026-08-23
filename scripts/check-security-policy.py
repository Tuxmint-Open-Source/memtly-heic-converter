#!/usr/bin/env python3
"""Validate the repository-local security policy contract."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / "SECURITY.md"

REQUIRED = [
    "## Supported versions",
    "`v0.1.0-rc.1`",
    "`main`",
    "no stable production release",
    "## Report a vulnerability privately",
    "/security/advisories/new",
    "Do not open a public issue",
    "minimum evidence",
    "exact project release, image digest, or full commit",
    "real hardware from emulation",
    "Do not send credentials",
    "personal photos",
    "EXIF/GPS metadata",
    "## Vulnerabilities in scope",
    "fail-closed conversion",
    "GitHub Actions",
    "immutable dependency pins",
    "## Not a private security report",
    "structured public issue forms",
    "## Coordinated disclosure",
    "not considered released merely because it exists on `main`",
    "## Security controls and limitations",
    "not production-ready",
    "real iPhone/iPad Safari validation remains outstanding",
    "not imply support or affiliation from Memtly",
]

FORBIDDEN = [
    "guaranteed secure",
    "production supported",
    "fully supported",
]


def main() -> int:
    failures: list[str] = []
    if not POLICY.is_file():
        failures.append("missing SECURITY.md")
    else:
        text = POLICY.read_text(encoding="utf-8")
        lowered = text.lower()
        for needle in REQUIRED:
            if needle.lower() not in lowered:
                failures.append(f"missing security-policy text: {needle}")
        for needle in FORBIDDEN:
            if needle.lower() in lowered:
                failures.append(f"forbidden security claim: {needle}")
        if "\t" in text:
            failures.append("tab characters are not allowed in SECURITY.md")

    if failures:
        print("security_policy=failed")
        print("\n".join(failures))
        return 1

    print(f"security_policy=passed assertions={len(REQUIRED) + len(FORBIDDEN)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
