"""Tests for logslice.bookmark_reporter."""

import json
from datetime import datetime, timezone

import pytest

from logslice.bookmarker import Bookmark
from logslice.bookmark_reporter import (
    format_bookmark_plain,
    format_bookmark_json,
    format_bookmark_list_plain,
    format_bookmark_list_json,
    report_bookmarks,
)


def _bm(name="mymark", filepath="/logs/app.log", offset=128, line_number=5):
    return Bookmark(
        name=name,
        filepath=filepath,
        offset=offset,
        line_number=line_number,
        created_at="2024-01-15T10:00:00+00:00",
    )


class TestFormatBookmarkPlain:
    def test_contains_name(self):
        assert "mymark" in format_bookmark_plain(_bm())

    def test_contains_filepath(self):
        assert "/logs/app.log" in format_bookmark_plain(_bm())

    def test_contains_line_number(self):
        assert "line 5" in format_bookmark_plain(_bm())

    def test_contains_offset(self):
        assert "offset 128" in format_bookmark_plain(_bm())

    def test_contains_timestamp(self):
        assert "2024-01-15" in format_bookmark_plain(_bm())


class TestFormatBookmarkJson:
    def test_is_valid_json(self):
        data = json.loads(format_bookmark_json(_bm()))
        assert isinstance(data, dict)

    def test_has_expected_keys(self):
        data = json.loads(format_bookmark_json(_bm()))
        assert "name" in data
        assert "offset" in data
        assert "line_number" in data

    def test_values_match(self):
        bm = _bm(name="x", offset=999)
        data = json.loads(format_bookmark_json(bm))
        assert data["name"] == "x"
        assert data["offset"] == 999


class TestFormatBookmarkListPlain:
    def test_empty_list_message(self):
        assert "No bookmarks" in format_bookmark_list_plain([])

    def test_header_present(self):
        result = format_bookmark_list_plain([_bm()])
        assert "Saved bookmarks" in result

    def test_each_bookmark_appears(self):
        bms = [_bm(name="a"), _bm(name="b")]
        result = format_bookmark_list_plain(bms)
        assert "[a]" in result
        assert "[b]" in result


class TestReportBookmarks:
    def test_plain_dispatch(self):
        result = report_bookmarks([], fmt="plain")
        assert "No bookmarks" in result

    def test_json_dispatch(self):
        result = report_bookmarks([_bm()], fmt="json")
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_default_is_plain(self):
        result = report_bookmarks([])
        assert "No bookmarks" in result
