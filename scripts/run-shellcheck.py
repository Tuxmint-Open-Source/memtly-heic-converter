#!/usr/bin/env python3
"""Acquire a verified ShellCheck release and scan tracked shell programs."""

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
VERSION = "0.11.0"
ARCHIVE_NAME = f"shellcheck-v{VERSION}.linux.x86_64.tar.xz"
DOWNLOAD_URL = (
    f"https://github.com/koalaman/shellcheck/releases/download/v{VERSION}/{ARCHIVE_NAME}"
)
ARCHIVE_SHA256 = "8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198"
ARCHIVE_ROOT = f"shellcheck-v{VERSION}"
ARCHIVE_MEMBERS = {
    f"{ARCHIVE_ROOT}/LICENSE.txt",
    f"{ARCHIVE_ROOT}/README.txt",
    f"{ARCHIVE_ROOT}/shellcheck",
}


class ShellCheckError(RuntimeError):
    """Raised when acquisition or inventory validation fails."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_archive(destination: Path) -> None:
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "memtly-heic-converter-shellcheck-gate"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        if response.status != 200:
            raise ShellCheckError(f"ShellCheck download returned HTTP {response.status}")
        with destination.open("xb") as output:
            shutil.copyfileobj(response, output)


def install_shellcheck(
    archive: Path,
    destination: Path,
    *,
    expected_sha256: str = ARCHIVE_SHA256,
) -> None:
    actual_sha256 = sha256(archive)
    if actual_sha256 != expected_sha256:
        raise ShellCheckError(
            f"ShellCheck archive checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    with tarfile.open(archive, mode="r:xz") as bundle:
        members = bundle.getmembers()
        names = {member.name for member in members}
        if names != ARCHIVE_MEMBERS:
            raise ShellCheckError(
                "ShellCheck archive inventory mismatch: " + ", ".join(sorted(names))
            )
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not member.isfile():
                raise ShellCheckError(f"unsafe ShellCheck archive member: {member.name}")

        binary_member = bundle.getmember(f"{ARCHIVE_ROOT}/shellcheck")
        source = bundle.extractfile(binary_member)
        if source is None:
            raise ShellCheckError("ShellCheck binary could not be read from archive")
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
    if f"version: {VERSION}" not in result.stdout:
        raise ShellCheckError(f"unexpected ShellCheck version output: {result.stdout.strip()}")


def tracked_shell_files(root: Path = ROOT) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.sh", "*.bash"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    relative_paths = [Path(raw.decode("utf-8")) for raw in result.stdout.split(b"\0") if raw]
    if not relative_paths:
        raise ShellCheckError("tracked shell inventory is empty")
    for relative in relative_paths:
        if relative.is_absolute() or ".." in relative.parts:
            raise ShellCheckError(f"unsafe tracked shell path: {relative}")
        if not (root / relative).is_file():
            raise ShellCheckError(f"tracked shell path is not a regular file: {relative}")
    return sorted(relative_paths)


def run_shellcheck(binary: Path, paths: list[Path], root: Path = ROOT) -> None:
    subprocess.run(
        [str(binary), "--severity=style", "--format=gcc", *map(str, paths)],
        cwd=root,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--archive", type=Path, help="Use an already downloaded pinned archive")
    source.add_argument("--shellcheck", type=Path, help="Use an existing ShellCheck binary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="memtly-shellcheck-") as temporary_dir:
        temporary = Path(temporary_dir)
        if args.shellcheck:
            binary = args.shellcheck.resolve()
        else:
            archive = args.archive.resolve() if args.archive else temporary / ARCHIVE_NAME
            if args.archive is None:
                download_archive(archive)
            binary = temporary / "shellcheck"
            install_shellcheck(archive, binary)
        verify_version(binary)
        paths = tracked_shell_files()
        run_shellcheck(binary, paths)
    print(f"shellcheck=passed version={VERSION} files={len(paths)} severity=style")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
