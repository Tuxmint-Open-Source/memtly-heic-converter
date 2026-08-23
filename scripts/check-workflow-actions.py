#!/usr/bin/env python3
"""Require immutable commit pins for every external GitHub Action."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
USES_PATTERN = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
IMMUTABLE_ACTION = re.compile(r"^[^/@\s]+/[^/@\s]+(?:/[^@\s]+)?@[0-9a-f]{40}$")


def main() -> int:
    failures: list[str] = []
    checked = 0

    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for match in USES_PATTERN.finditer(text):
            reference = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            if reference.startswith("./") or reference.startswith("docker://"):
                continue
            checked += 1
            if not IMMUTABLE_ACTION.fullmatch(reference):
                failures.append(
                    f"{path.relative_to(ROOT)}:{line}: external Action is not pinned "
                    f"to a lowercase 40-character commit: {reference}"
                )

    if checked == 0:
        failures.append("no external GitHub Actions were found")

    if failures:
        print("workflow_action_pins=failed")
        print("\n".join(failures))
        return 1

    print(f"workflow_action_pins=passed references={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
