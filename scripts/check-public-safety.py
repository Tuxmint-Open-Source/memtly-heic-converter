#!/usr/bin/env python3
"""Fail when public repository files contain common private/sensitive markers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()
SKIP = {ROOT / "AGENTS.md", SELF}
PATTERNS = {
    "private key": re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "private IPv4 10/8": re.compile(r"(?<![0-9])10(?:\.[0-9]{1,3}){3}(?![0-9])"),
    "private IPv4 172.16/12": re.compile(r"(?<![0-9])172\.(?:1[6-9]|2[0-9]|3[01])(?:\.[0-9]{1,3}){2}(?![0-9])"),
    "private IPv4 192.168/16": re.compile(r"(?<![0-9])192\.168(?:\.[0-9]{1,3}){2}(?![0-9])"),
    "private Gitea marker": re.compile(r"gitea\.rueti", re.IGNORECASE),
    "private lab marker": re.compile(r"proxmox", re.IGNORECASE),
}


def repository_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return [ROOT / item.decode() for item in output.split(b"\0") if item]


def main() -> int:
    findings: list[str] = []
    for path in repository_files():
        if path in SKIP or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data[:4096]:
            continue
        text = data.decode("utf-8", errors="ignore")
        relative = path.relative_to(ROOT)
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{relative}:{line_number}: {label}")

    if findings:
        print("public_safety_scan=failed")
        print("\n".join(findings))
        return 1

    print("public_safety_scan=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
