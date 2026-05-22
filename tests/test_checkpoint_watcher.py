"""Tests for logslice.checkpoint_watcher.resume_and_watch."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from logslice.checkpoint import load_checkpoint, save_checkpoint
from logslice.checkpoint_watcher import resume_and_watch
from logslice.config import LogSliceConfig


def _cfg(**kwargs) -> LogSliceConfig:
    defaults = dict(
        input=None,
        format="plain",
        highlight=False,
        include_patterns=[],
        exclude_patterns=[],
        start=None,
        end=None,
    )
    defaults.update(kwargs)
    return LogSliceConfig(**defaults)


class TestResumeAndWatch:
    def test_replays_missed_lines(self, tmp_path):
        d = tmp_path / "cp"
        d.mkdir()
        log = tmp_path / "app.log"
        log.write_text("old1\nold2\n")
        # Simulate checkpoint at start of file (nothing consumed yet)
        save_checkpoint(str(log), 0, checkpoint_dir=d)

        gen = resume_and_watch(str(log), _cfg(), checkpoint_dir=d)
        # Collect replay batch then stop (don't enter live tail)
        results = []
        # We need to consume only the replay part; patch sleep to raise
        import logslice.checkpoint_watcher as cw
        original_sleep = time.sleep

        def _stop(_):
            raise StopIteration

        import unittest.mock as mock
        with mock.patch("time.sleep", side_effect=StopIteration):
            try:
                for line in gen:
                    results.append(line)
            except StopIteration:
                pass

        assert "old1\n" in results
        assert "old2\n" in results

    def test_checkpoint_updated_after_replay(self, tmp_path):
        d = tmp_path / "cp"
        d.mkdir()
        log = tmp_path / "app.log"
        log.write_text("aaa\nbbb\n")
        save_checkpoint(str(log), 0, checkpoint_dir=d)

        import unittest.mock as mock
        with mock.patch("time.sleep", side_effect=StopIteration):
            try:
                list(resume_and_watch(str(log), _cfg(), checkpoint_dir=d))
            except StopIteration:
                pass

        offset = load_checkpoint(str(log), checkpoint_dir=d)
        assert offset == log.stat().st_size

    def test_include_filter_applied_during_replay(self, tmp_path):
        d = tmp_path / "cp"
        d.mkdir()
        log = tmp_path / "app.log"
        log.write_text("ERROR something\nDEBUG noise\nERROR again\n")
        save_checkpoint(str(log), 0, checkpoint_dir=d)

        cfg = _cfg(include_patterns=["ERROR"])
        results = []
        import unittest.mock as mock
        with mock.patch("time.sleep", side_effect=StopIteration):
            try:
                for line in resume_and_watch(str(log), cfg, checkpoint_dir=d):
                    results.append(line)
            except StopIteration:
                pass

        assert all("ERROR" in r for r in results)
        assert len(results) == 2
