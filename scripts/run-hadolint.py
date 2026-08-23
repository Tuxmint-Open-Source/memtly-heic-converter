#!/usr/bin/env python3
"""Acquire verified hadolint and scan every tracked Dockerfile."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "2.15.1"
BINARY_NAME = "hadolint-linux-x86_64"
DOWNLOAD_URL = f"https://github.com/hadolint/hadolint/releases/download/v{VERSION}/{BINARY_NAME}"
BINARY_SHA256 = "c7187db94eeeeca956519a6af171adc31453941a1e777961f6e680f697c8c507"
CONFIG = Path(".hadolint.yaml")


class HadolintError(RuntimeError):
    """Raised when acquisition or Dockerfile inventory validation fails."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_binary(destination: Path) -> None:
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "memtly-heic-converter-hadolint-gate"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        if response.status != 200:
            raise HadolintError(f"hadolint download returned HTTP {response.status}")
        with destination.open("xb") as output:
            shutil.copyfileobj(response, output)


def install_hadolint(
    source: Path,
    destination: Path,
    *,
    expected_sha256: str = BINARY_SHA256,
) -> None:
    actual_sha256 = sha256(source)
    if actual_sha256 != expected_sha256:
        raise HadolintError(
            f"hadolint checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        with source.open("rb") as input_file, temporary.open("xb") as output:
            shutil.copyfileobj(input_file, output)
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
    if result.stdout.strip() != f"Haskell Dockerfile Linter {VERSION}":
        raise HadolintError(f"unexpected hadolint version output: {result.stdout.strip()}")


def tracked_dockerfiles(root: Path = ROOT) -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            ":(glob)Dockerfile",
            ":(glob)Dockerfile.*",
            ":(glob)**/Dockerfile",
            ":(glob)**/Dockerfile.*",
        ],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    relative_paths = sorted(
        {Path(raw.decode("utf-8")) for raw in result.stdout.split(b"\0") if raw}
    )
    if not relative_paths:
        raise HadolintError("tracked Dockerfile inventory is empty")
    for relative in relative_paths:
        if relative.is_absolute() or ".." in relative.parts:
            raise HadolintError(f"unsafe tracked Dockerfile path: {relative}")
        if not (relative.name == "Dockerfile" or relative.name.startswith("Dockerfile.")):
            raise HadolintError(f"unexpected tracked Dockerfile name: {relative}")
        if not (root / relative).is_file():
            raise HadolintError(f"tracked Dockerfile is not a regular file: {relative}")
    return relative_paths


def run_hadolint(binary: Path, paths: list[Path], root: Path = ROOT) -> None:
    config = root / CONFIG
    if not config.is_file():
        raise HadolintError(f"missing hadolint config: {CONFIG}")
    subprocess.run(
        [
            str(binary),
            "--config",
            str(CONFIG),
            "--failure-threshold",
            "style",
            "--format",
            "tty",
            *map(str, paths),
        ],
        cwd=root,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--download", type=Path, help="Use an already downloaded pinned binary")
    source.add_argument("--hadolint", type=Path, help="Use an existing hadolint binary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="memtly-hadolint-") as temporary_dir:
        temporary = Path(temporary_dir)
        if args.hadolint:
            binary = args.hadolint.resolve()
        else:
            download = args.download.resolve() if args.download else temporary / BINARY_NAME
            if args.download is None:
                download_binary(download)
            binary = temporary / "hadolint"
            install_hadolint(download, binary)
        verify_version(binary)
        paths = tracked_dockerfiles()
        run_hadolint(binary, paths)
    print(f"hadolint=passed version={VERSION} dockerfiles={len(paths)} threshold=style")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
