"""Regression tests for verified ShellCheck acquisition and inventory."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-shellcheck.py"
SPEC = importlib.util.spec_from_file_location("run_shellcheck", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_archive(path: Path, *, unsafe: bool = False) -> str:
    binary = b"#!/usr/bin/env sh\nprintf 'ShellCheck - shell script analysis tool\\nversion: 0.11.0\\n'\n"
    with tarfile.open(path, mode="w:xz") as bundle:
        payloads = {
            f"{MODULE.ARCHIVE_ROOT}/LICENSE.txt": b"test license\n",
            f"{MODULE.ARCHIVE_ROOT}/README.txt": b"test readme\n",
            f"{MODULE.ARCHIVE_ROOT}/shellcheck": binary,
        }
        for name, payload in payloads.items():
            member = tarfile.TarInfo(name)
            member.mode = 0o755 if name.endswith("/shellcheck") else 0o644
            member.size = len(payload)
            bundle.addfile(member, io.BytesIO(payload))
        if unsafe:
            member = tarfile.TarInfo(f"{MODULE.ARCHIVE_ROOT}/../escape")
            member.size = 1
            bundle.addfile(member, io.BytesIO(b"x"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VerifiedAcquisitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = self.root / "shellcheck.tar.xz"
        self.binary = self.root / "bin" / "shellcheck"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_verified_archive_installs_exact_binary(self) -> None:
        digest = make_archive(self.archive)
        MODULE.install_shellcheck(self.archive, self.binary, expected_sha256=digest)
        self.assertTrue(self.binary.is_file())
        self.assertEqual(self.binary.stat().st_mode & 0o777, 0o755)
        MODULE.verify_version(self.binary)

    def test_checksum_failure_stops_before_archive_parsing(self) -> None:
        self.archive.write_bytes(b"not a tar archive")
        with self.assertRaisesRegex(MODULE.ShellCheckError, "checksum mismatch"):
            MODULE.install_shellcheck(self.archive, self.binary, expected_sha256="0" * 64)
        self.assertFalse(self.binary.exists())

    def test_unsafe_or_unexpected_archive_inventory_is_rejected(self) -> None:
        digest = make_archive(self.archive, unsafe=True)
        with self.assertRaisesRegex(MODULE.ShellCheckError, "inventory mismatch"):
            MODULE.install_shellcheck(self.archive, self.binary, expected_sha256=digest)
        self.assertFalse(self.binary.exists())

    def test_tracked_inventory_comes_from_git_and_ignores_untracked_files(self) -> None:
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True)
        (self.root / "tracked.sh").write_text("#!/usr/bin/env bash\ntrue\n")
        (self.root / "tracked.bash").write_text("true\n")
        (self.root / "ignored.sh").write_text("false\n")
        (self.root / "notes.txt").write_text("not shell\n")
        subprocess.run(
            ["git", "add", "tracked.sh", "tracked.bash", "notes.txt"],
            cwd=self.root,
            check=True,
        )
        self.assertEqual(
            MODULE.tracked_shell_files(self.root),
            [Path("tracked.bash"), Path("tracked.sh")],
        )


if __name__ == "__main__":
    unittest.main()
