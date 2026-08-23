#!/usr/bin/env python3
"""Acquire a verified Ruff release and lint tracked Python programs."""

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
VERSION = "0.16.4"
ARCHIVE_NAME = "ruff-x86_64-unknown-linux-gnu.tar.gz"
DOWNLOAD_URL = f"https://github.com/astral-sh/ruff/releases/download/{VERSION}/{ARCHIVE_NAME}"
ARCHIVE_SHA256 = "9cb1234804ddb0f7f57cef3f81623ce5acb990e40af7cce08dc7778c9d7ee96c"
ARCHIVE_DIRECTORY = "ruff-x86_64-unknown-linux-gnu"
ARCHIVE_BINARY = f"{ARCHIVE_DIRECTORY}/ruff"
RULES = "E4,E7,E9,F,I,EXE,B,UP"


class RuffError(RuntimeError):
    """Raised when acquisition or Python inventory validation fails."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_archive(destination: Path) -> None:
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "memtly-heic-converter-ruff-gate"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuffError(f"Ruff download returned HTTP {response.status}")
        with destination.open("xb") as output:
            shutil.copyfileobj(response, output)


def install_ruff(
    archive: Path,
    destination: Path,
    *,
    expected_sha256: str = ARCHIVE_SHA256,
) -> None:
    actual_sha256 = sha256(archive)
    if actual_sha256 != expected_sha256:
        raise RuffError(
            f"Ruff archive checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    with tarfile.open(archive, mode="r:gz") as bundle:
        members = bundle.getmembers()
        names = {member.name for member in members}
        if names != {ARCHIVE_DIRECTORY, ARCHIVE_BINARY}:
            raise RuffError("Ruff archive inventory mismatch: " + ", ".join(sorted(names)))
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise RuffError(f"unsafe Ruff archive member: {member.name}")
        directory = bundle.getmember(ARCHIVE_DIRECTORY)
        binary = bundle.getmember(ARCHIVE_BINARY)
        if not directory.isdir() or not binary.isfile():
            raise RuffError("Ruff archive member types are invalid")

        source = bundle.extractfile(binary)
        if source is None:
            raise RuffError("Ruff binary could not be read from archive")
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
        [str(binary), "--version"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.stdout.strip() != f"ruff {VERSION}":
        raise RuffError(f"unexpected Ruff version output: {result.stdout.strip()}")


def tracked_python(root: Path = ROOT) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.py"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    relative_paths = [Path(raw.decode("utf-8")) for raw in result.stdout.split(b"\0") if raw]
    if not relative_paths:
        raise RuffError("tracked Python inventory is empty")
    for relative in relative_paths:
        if relative.is_absolute() or ".." in relative.parts:
            raise RuffError(f"unsafe tracked Python path: {relative}")
        if relative.suffix != ".py" or not (root / relative).is_file():
            raise RuffError(f"tracked Python path is invalid: {relative}")
    return sorted(relative_paths)


def run_ruff(binary: Path, paths: list[Path], root: Path = ROOT) -> None:
    subprocess.run(
        [
            str(binary),
            "check",
            "--no-cache",
            "--output-format=concise",
            "--select",
            RULES,
            *map(str, paths),
        ],
        cwd=root,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--archive", type=Path, help="Use an already downloaded pinned archive")
    source.add_argument("--ruff", type=Path, help="Use an existing Ruff binary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="memtly-ruff-") as temporary_dir:
        temporary = Path(temporary_dir)
        if args.ruff:
            binary = args.ruff.resolve()
        else:
            archive = args.archive.resolve() if args.archive else temporary / ARCHIVE_NAME
            if args.archive is None:
                download_archive(archive)
            binary = temporary / "ruff"
            install_ruff(archive, binary)
        verify_version(binary)
        paths = tracked_python()
        run_ruff(binary, paths)
    print(f"ruff=passed version={VERSION} python_files={len(paths)} rules={RULES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
