"""Tests for logslice.bookmarker."""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from logslice.bookmarker import (
    Bookmark,
    save_bookmark,
    load_bookmark,
    delete_bookmark,
    list_bookmarks,
    read_from_bookmark,
)


def _bm(name="test", filepath="/var/log/app.log", offset=0, line_number=1):
    return Bookmark(
        name=name,
        filepath=filepath,
        offset=offset,
        line_number=line_number,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


class TestBookmarkRoundTrip:
    def test_save_and_load(self, tmp_path):
        bm = _bm()
        save_bookmark(bm, directory=tmp_path)
        loaded = load_bookmark("test", directory=tmp_path)
        assert loaded is not None
        assert loaded.name == bm.name
        assert loaded.offset == bm.offset

    def test_missing_returns_none(self, tmp_path):
        result = load_bookmark("nonexistent", directory=tmp_path)
        assert result is None

    def test_overwrite_updates(self, tmp_path):
        bm1 = _bm(offset=0)
        bm2 = _bm(offset=512)
        save_bookmark(bm1, directory=tmp_path)
        save_bookmark(bm2, directory=tmp_path)
        loaded = load_bookmark("test", directory=tmp_path)
        assert loaded.offset == 512

    def test_to_dict_from_dict_roundtrip(self):
        bm = _bm(name="alpha", offset=99, line_number=7)
        assert Bookmark.from_dict(bm.to_dict()) == bm


class TestDeleteBookmark:
    def test_delete_existing_returns_true(self, tmp_path):
        save_bookmark(_bm(), directory=tmp_path)
        assert delete_bookmark("test", directory=tmp_path) is True

    def test_delete_missing_returns_false(self, tmp_path):
        assert delete_bookmark("ghost", directory=tmp_path) is False

    def test_deleted_bookmark_not_loadable(self, tmp_path):
        save_bookmark(_bm(), directory=tmp_path)
        delete_bookmark("test", directory=tmp_path)
        assert load_bookmark("test", directory=tmp_path) is None


class TestListBookmarks:
    def test_empty_dir_returns_empty(self, tmp_path):
        assert list_bookmarks(directory=tmp_path) == []

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        missing = tmp_path / "no_such_dir"
        assert list_bookmarks(directory=missing) == []

    def test_returns_all_saved(self, tmp_path):
        for name in ("alpha", "beta", "gamma"):
            save_bookmark(_bm(name=name), directory=tmp_path)
        result = list_bookmarks(directory=tmp_path)
        assert len(result) == 3
        assert {bm.name for bm in result} == {"alpha", "beta", "gamma"}

    def test_sorted_by_name(self, tmp_path):
        for name in ("z", "a", "m"):
            save_bookmark(_bm(name=name), directory=tmp_path)
        names = [bm.name for bm in list_bookmarks(directory=tmp_path)]
        assert names == sorted(names)


class TestReadFromBookmark:
    def test_reads_from_offset(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("line1\nline2\nline3\n")
        offset = len("line1\n")
        bm = _bm(filepath=str(log), offset=offset, line_number=2)
        lines = list(read_from_bookmark(str(log), bm))
        assert lines[0].strip() == "line2"
        assert lines[1].strip() == "line3"

    def test_offset_zero_reads_all(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("a\nb\nc\n")
        bm = _bm(filepath=str(log), offset=0)
        lines = list(read_from_bookmark(str(log), bm))
        assert len(lines) == 3
