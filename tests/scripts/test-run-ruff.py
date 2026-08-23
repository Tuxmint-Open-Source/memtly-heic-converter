"""Regression tests for verified Ruff acquisition and Python inventory."""

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
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-ruff.py"
SPEC = importlib.util.spec_from_file_location("run_ruff", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_archive(path: Path, *, unsafe: bool = False) -> str:
    binary = b"#!/usr/bin/env sh\nprintf 'ruff 0.16.4\\n'\n"
    with tarfile.open(path, mode="w:gz") as bundle:
        directory = tarfile.TarInfo(MODULE.ARCHIVE_DIRECTORY)
        directory.type = tarfile.DIRTYPE
        directory.mode = 0o755
        bundle.addfile(directory)

        member = tarfile.TarInfo(MODULE.ARCHIVE_BINARY)
        member.mode = 0o755
        member.size = len(binary)
        bundle.addfile(member, io.BytesIO(binary))
        if unsafe:
            escape = tarfile.TarInfo("../escape")
            escape.size = 1
            bundle.addfile(escape, io.BytesIO(b"x"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VerifiedRuffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = self.root / "ruff.tar.gz"
        self.binary = self.root / "bin" / "ruff"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_verified_archive_installs_exact_binary(self) -> None:
        digest = make_archive(self.archive)
        MODULE.install_ruff(self.archive, self.binary, expected_sha256=digest)
        self.assertTrue(self.binary.is_file())
        self.assertEqual(self.binary.stat().st_mode & 0o777, 0o755)
        MODULE.verify_version(self.binary)

    def test_checksum_failure_stops_before_archive_parsing(self) -> None:
        self.archive.write_bytes(b"not a tar archive")
        with self.assertRaisesRegex(MODULE.RuffError, "checksum mismatch"):
            MODULE.install_ruff(self.archive, self.binary, expected_sha256="0" * 64)
        self.assertFalse(self.binary.exists())

    def test_unsafe_or_unexpected_archive_inventory_is_rejected(self) -> None:
        digest = make_archive(self.archive, unsafe=True)
        with self.assertRaisesRegex(MODULE.RuffError, "inventory mismatch"):
            MODULE.install_ruff(self.archive, self.binary, expected_sha256=digest)
        self.assertFalse(self.binary.exists())

    def test_tracked_python_inventory_excludes_untracked_files(self) -> None:
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True)
        tracked = self.root / "tracked.py"
        nested = self.root / "nested" / "also.py"
        nested.parent.mkdir()
        tracked.write_text("pass\n")
        nested.write_text("pass\n")
        (self.root / "untracked.py").write_text("pass\n")
        (self.root / "other.txt").write_text("pass\n")
        subprocess.run(
            ["git", "add", "tracked.py", "nested/also.py", "other.txt"],
            cwd=self.root,
            check=True,
        )
        self.assertEqual(
            MODULE.tracked_python(self.root),
            [Path("nested/also.py"), Path("tracked.py")],
        )

    def test_invocation_pins_rules_output_and_cache_behavior(self) -> None:
        with mock.patch.object(MODULE.subprocess, "run") as run:
            MODULE.run_ruff(Path("/verified/ruff"), [Path("scripts/test.py")], self.root)
        run.assert_called_once_with(
            [
                "/verified/ruff",
                "check",
                "--no-cache",
                "--output-format=concise",
                "--select",
                "E4,E7,E9,F,I,EXE,B,UP",
                "scripts/test.py",
            ],
            cwd=self.root,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
