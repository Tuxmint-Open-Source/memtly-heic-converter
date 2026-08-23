#!/usr/bin/env python3
"""Acquire a verified actionlint release and validate tracked workflows."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.7.12"
ARCHIVE_NAME = f"actionlint_{VERSION}_linux_amd64.tar.gz"
DOWNLOAD_URL = f"https://github.com/rhysd/actionlint/releases/download/v{VERSION}/{ARCHIVE_NAME}"
ARCHIVE_SHA256 = "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"
ARCHIVE_MEMBERS = {
    "LICENSE.txt",
    "README.md",
    "actionlint",
    "docs/README.md",
    "docs/api.md",
    "docs/checks.md",
    "docs/config.md",
    "docs/install.md",
    "docs/reference.md",
    "docs/usage.md",
    "man/actionlint.1",
}


class ActionlintError(RuntimeError):
    """Raised when acquisition or workflow inventory validation fails."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_archive(destination: Path) -> None:
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "memtly-heic-converter-actionlint-gate"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        if response.status != 200:
            raise ActionlintError(f"actionlint download returned HTTP {response.status}")
        with destination.open("xb") as output:
            shutil.copyfileobj(response, output)


def install_actionlint(
    archive: Path,
    destination: Path,
    *,
    expected_sha256: str = ARCHIVE_SHA256,
) -> None:
    actual_sha256 = sha256(archive)
    if actual_sha256 != expected_sha256:
        raise ActionlintError(
            f"actionlint archive checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    with tarfile.open(archive, mode="r:gz") as bundle:
        members = bundle.getmembers()
        names = {member.name for member in members}
        if names != ARCHIVE_MEMBERS:
            raise ActionlintError(
                "actionlint archive inventory mismatch: " + ", ".join(sorted(names))
            )
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not member.isfile():
                raise ActionlintError(f"unsafe actionlint archive member: {member.name}")

        source = bundle.extractfile(bundle.getmember("actionlint"))
        if source is None:
            raise ActionlintError("actionlint binary could not be read from archive")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        try:
            with temporary.open("xb") as output:
                shutil.copyfileobj(source, output)
            temporary.chmod(0o755)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)


def verify_version(binary: Path) -> None:
    result = subprocess.run(
        [str(binary), "-version"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.stdout.splitlines()[0].strip() != VERSION:
        raise ActionlintError(f"unexpected actionlint version output: {result.stdout.strip()}")


def tracked_workflows(root: Path = ROOT) -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
        ],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    relative_paths = [Path(raw.decode("utf-8")) for raw in result.stdout.split(b"\0") if raw]
    if not relative_paths:
        raise ActionlintError("tracked workflow inventory is empty")
    for relative in relative_paths:
        if relative.is_absolute() or ".." in relative.parts:
            raise ActionlintError(f"unsafe tracked workflow path: {relative}")
        if relative.parent != Path(".github/workflows"):
            raise ActionlintError(f"workflow escaped expected directory: {relative}")
        if relative.suffix not in {".yml", ".yaml"} or not (root / relative).is_file():
            raise ActionlintError(f"tracked workflow path is invalid: {relative}")
    return sorted(relative_paths)


def run_actionlint(binary: Path, paths: list[Path], root: Path = ROOT) -> None:
    subprocess.run(
        [
            str(binary),
            "-no-color",
            "-shellcheck=",
            "-pyflakes=",
            *map(str, paths),
        ],
        cwd=root,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--archive", type=Path, help="Use an already downloaded pinned archive")
    source.add_argument("--actionlint", type=Path, help="Use an existing actionlint binary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="memtly-actionlint-") as temporary_dir:
        temporary = Path(temporary_dir)
        if args.actionlint:
            binary = args.actionlint.resolve()
        else:
            archive = args.archive.resolve() if args.archive else temporary / ARCHIVE_NAME
            if args.archive is None:
                download_archive(archive)
            binary = temporary / "actionlint"
            install_actionlint(archive, binary)
        verify_version(binary)
        paths = tracked_workflows()
        run_actionlint(binary, paths)
    print(f"actionlint=passed version={VERSION} workflows={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
