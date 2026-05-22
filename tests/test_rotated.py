"""Tests for logslice.rotated — rotation-aware log reader."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from logslice.rotated import _get_inode, _get_size, read_with_rotation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: str, text: str, mode: str = "w") -> None:
    with open(path, mode) as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# _get_inode
# ---------------------------------------------------------------------------

class TestGetInode:
    def test_returns_int_for_existing_file(self, tmp_path):
        p = tmp_path / "a.log"
        p.write_text("x")
        assert isinstance(_get_inode(str(p)), int)

    def test_returns_none_for_missing_file(self, tmp_path):
        assert _get_inode(str(tmp_path / "ghost.log")) is None


# ---------------------------------------------------------------------------
# _get_size
# ---------------------------------------------------------------------------

class TestGetSize:
    def test_returns_zero_for_missing_file(self, tmp_path):
        assert _get_size(str(tmp_path / "nope.log")) == 0

    def test_returns_correct_size(self, tmp_path):
        p = tmp_path / "b.log"
        p.write_text("hello")
        assert _get_size(str(p)) == 5


# ---------------------------------------------------------------------------
# read_with_rotation
# ---------------------------------------------------------------------------

class TestReadWithRotation:
    def test_reads_all_lines_no_rotation(self, tmp_path):
        p = tmp_path / "app.log"
        _write(str(p), "line1\nline2\nline3\n")
        results = list(read_with_rotation(str(p)))
        lines = [r[0] for r in results]
        assert lines == ["line1\n", "line2\n", "line3\n"]

    def test_yields_correct_offsets(self, tmp_path):
        p = tmp_path / "app.log"
        _write(str(p), "ab\ncd\n")
        results = list(read_with_rotation(str(p)))
        # Each offset should be strictly increasing.
        offsets = [r[1] for r in results]
        assert offsets == sorted(offsets)
        assert offsets[-1] == p.stat().st_size

    def test_start_offset_skips_bytes(self, tmp_path):
        p = tmp_path / "app.log"
        _write(str(p), "skip\nkeep\n")
        skip_len = len("skip\n")
        results = list(read_with_rotation(str(p), start_offset=skip_len))
        lines = [r[0] for r in results]
        assert lines == ["keep\n"]

    def test_detects_truncation_as_rotation(self, tmp_path):
        p = tmp_path / "app.log"
        _write(str(p), "old_line\n")
        # Read the first line to advance the offset.
        gen = read_with_rotation(str(p))
        first_line, offset = next(gen)
        assert first_line == "old_line\n"

        # Simulate rotation by truncating and writing new content.
        _write(str(p), "new_line\n")  # overwrites — size may be same or smaller
        results = list(gen)
        lines = [r[0] for r in results]
        assert "new_line\n" in lines

    def test_empty_file_yields_nothing(self, tmp_path):
        p = tmp_path / "empty.log"
        p.write_text("")
        assert list(read_with_rotation(str(p))) == []
