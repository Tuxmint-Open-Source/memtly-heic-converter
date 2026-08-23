#!/usr/bin/env python3
"""Regression tests for verified hadolint acquisition and Dockerfile inventory."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-hadolint.py"
SPEC = importlib.util.spec_from_file_location("run_hadolint", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class VerifiedHadolintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.download = self.root / "hadolint.download"
        self.binary = self.root / "bin" / "hadolint"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_verified_download_installs_exact_binary(self) -> None:
        payload = b"#!/usr/bin/env sh\nprintf 'Haskell Dockerfile Linter 2.15.1\\n'\n"
        self.download.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        MODULE.install_hadolint(self.download, self.binary, expected_sha256=digest)
        self.assertEqual(self.binary.read_bytes(), payload)
        self.assertEqual(self.binary.stat().st_mode & 0o777, 0o755)
        MODULE.verify_version(self.binary)

    def test_checksum_failure_stops_before_installation(self) -> None:
        self.download.write_bytes(b"unverified")
        with self.assertRaisesRegex(MODULE.HadolintError, "checksum mismatch"):
            MODULE.install_hadolint(self.download, self.binary, expected_sha256="0" * 64)
        self.assertFalse(self.binary.exists())

    def test_tracked_inventory_includes_nested_variants_only(self) -> None:
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True)
        nested = self.root / "images"
        nested.mkdir()
        tracked = [
            self.root / "Dockerfile",
            self.root / "Dockerfile.dev",
            nested / "Dockerfile",
            nested / "Dockerfile.test",
        ]
        for path in tracked:
            path.write_text("FROM scratch\n")
        (self.root / "Dockerfile.untracked").write_text("FROM scratch\n")
        (self.root / "NotDockerfile").write_text("FROM scratch\n")
        subprocess.run(
            ["git", "add", *[str(path.relative_to(self.root)) for path in tracked], "NotDockerfile"],
            cwd=self.root,
            check=True,
        )
        self.assertEqual(
            MODULE.tracked_dockerfiles(self.root),
            [
                Path("Dockerfile"),
                Path("Dockerfile.dev"),
                Path("images/Dockerfile"),
                Path("images/Dockerfile.test"),
            ],
        )

    def test_invocation_uses_exact_config_threshold_and_inventory(self) -> None:
        (self.root / MODULE.CONFIG).write_text("ignored:\n  - DL3059\n")
        with mock.patch.object(MODULE.subprocess, "run") as run:
            MODULE.run_hadolint(
                Path("/verified/hadolint"),
                [Path("Dockerfile"), Path("images/Dockerfile.test")],
                self.root,
            )
        run.assert_called_once_with(
            [
                "/verified/hadolint",
                "--config",
                ".hadolint.yaml",
                "--failure-threshold",
                "style",
                "--format",
                "tty",
                "Dockerfile",
                "images/Dockerfile.test",
            ],
            cwd=self.root,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
