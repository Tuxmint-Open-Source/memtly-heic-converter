#!/usr/bin/env python3
"""Regression tests for verified actionlint acquisition and workflow inventory."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-actionlint.py"
SPEC = importlib.util.spec_from_file_location("run_actionlint", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_archive(path: Path, *, unsafe: bool = False) -> str:
    binary = b"#!/usr/bin/env sh\nprintf '1.7.12\\ntest build\\n'\n"
    payloads = {name: b"test\n" for name in MODULE.ARCHIVE_MEMBERS}
    payloads["actionlint"] = binary
    if unsafe:
        payloads["../escape"] = b"x"
    with tarfile.open(path, mode="w:gz") as bundle:
        for name, payload in payloads.items():
            member = tarfile.TarInfo(name)
            member.mode = 0o755 if name == "actionlint" else 0o644
            member.size = len(payload)
            bundle.addfile(member, io.BytesIO(payload))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VerifiedActionlintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = self.root / "actionlint.tar.gz"
        self.binary = self.root / "bin" / "actionlint"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_verified_archive_installs_exact_binary(self) -> None:
        digest = make_archive(self.archive)
        MODULE.install_actionlint(self.archive, self.binary, expected_sha256=digest)
        self.assertTrue(self.binary.is_file())
        self.assertEqual(self.binary.stat().st_mode & 0o777, 0o755)
        MODULE.verify_version(self.binary)

    def test_checksum_failure_stops_before_archive_parsing(self) -> None:
        self.archive.write_bytes(b"not a tar archive")
        with self.assertRaisesRegex(MODULE.ActionlintError, "checksum mismatch"):
            MODULE.install_actionlint(self.archive, self.binary, expected_sha256="0" * 64)
        self.assertFalse(self.binary.exists())

    def test_unsafe_or_unexpected_archive_inventory_is_rejected(self) -> None:
        digest = make_archive(self.archive, unsafe=True)
        with self.assertRaisesRegex(MODULE.ActionlintError, "inventory mismatch"):
            MODULE.install_actionlint(self.archive, self.binary, expected_sha256=digest)
        self.assertFalse(self.binary.exists())

    def test_tracked_workflow_inventory_excludes_untracked_and_other_yaml(self) -> None:
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True)
        workflows = self.root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "tracked.yml").write_text("name: tracked\n")
        (workflows / "tracked.yaml").write_text("name: tracked too\n")
        (workflows / "untracked.yml").write_text("name: untracked\n")
        (self.root / "other.yml").write_text("not a workflow\n")
        subprocess.run(
            [
                "git",
                "add",
                ".github/workflows/tracked.yml",
                ".github/workflows/tracked.yaml",
                "other.yml",
            ],
            cwd=self.root,
            check=True,
        )
        self.assertEqual(
            MODULE.tracked_workflows(self.root),
            [
                Path(".github/workflows/tracked.yaml"),
                Path(".github/workflows/tracked.yml"),
            ],
        )

    def test_invocation_disables_color_and_optional_external_linters(self) -> None:
        with mock.patch.object(MODULE.subprocess, "run") as run:
            MODULE.run_actionlint(Path("/verified/actionlint"), [Path(".github/workflows/test.yml")], self.root)
        run.assert_called_once_with(
            [
                "/verified/actionlint",
                "-no-color",
                "-shellcheck=",
                "-pyflakes=",
                ".github/workflows/test.yml",
            ],
            cwd=self.root,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
