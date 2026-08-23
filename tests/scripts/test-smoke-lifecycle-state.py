#!/usr/bin/env python3
"""Regression tests for lifecycle state-file handling."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "smoke-lifecycle.py"
SPEC = importlib.util.spec_from_file_location("smoke_lifecycle", MODULE_PATH)
assert SPEC and SPEC.loader
SMOKE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SMOKE
SPEC.loader.exec_module(SMOKE)


class LifecycleStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "state.json"
        self.previous = getattr(SMOKE, "STATE_FILE")
        self.previous_new_secret = getattr(SMOKE, "NEW_GALLERY_SECRET_KEY")
        setattr(SMOKE, "STATE_FILE", str(self.path))

    def tearDown(self) -> None:
        setattr(SMOKE, "STATE_FILE", self.previous)
        setattr(SMOKE, "NEW_GALLERY_SECRET_KEY", self.previous_new_secret)
        self.temporary.cleanup()

    def test_round_trip_excludes_secret_and_uses_owner_only_mode(self) -> None:
        SMOKE.save_state_file(42, "generated-identifier")

        self.assertEqual(SMOKE.load_state_file(), ("42", "generated-identifier"))
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(
            json.loads(self.path.read_text()),
            {"gallery_id": 42, "gallery_identifier": "generated-identifier"},
        )
        self.assertNotIn("secret", self.path.read_text().lower())

    def test_caller_supplied_secret_is_not_part_of_state_contract(self) -> None:
        setattr(SMOKE, "NEW_GALLERY_SECRET_KEY", "caller-held-secret")
        try:
            SMOKE.save_state_file(43, "caller-held")
            self.assertEqual(SMOKE.load_state_file(), ("43", "caller-held"))
            self.assertNotIn("caller-held-secret", self.path.read_text())
        finally:
            setattr(SMOKE, "NEW_GALLERY_SECRET_KEY", "")

    def test_rejects_group_or_world_accessible_state(self) -> None:
        self.path.write_text('{"gallery_id": 42, "gallery_identifier": "generated"}')
        self.path.chmod(0o644)

        with self.assertRaisesRegex(RuntimeError, "only by its owner"):
            SMOKE.load_state_file()

    def test_rejects_symlink_state(self) -> None:
        target = self.path.with_name("target.json")
        target.write_text('{"gallery_id": 42, "gallery_identifier": "generated"}')
        target.chmod(0o600)
        os.symlink(target, self.path)

        with self.assertRaisesRegex(RuntimeError, "regular file"):
            SMOKE.load_state_file()

    def test_atomic_save_replaces_destination_symlink_not_target(self) -> None:
        target = self.path.with_name("target.json")
        target.write_text("unchanged")
        os.symlink(target, self.path)

        SMOKE.save_state_file(7, "replacement")

        self.assertFalse(self.path.is_symlink())
        self.assertEqual(target.read_text(), "unchanged")
        self.assertEqual(SMOKE.load_state_file(), ("7", "replacement"))


if __name__ == "__main__":
    unittest.main()