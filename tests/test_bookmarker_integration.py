"""Integration tests: bookmarker + reporter together."""

import json
from datetime import datetime, timezone
from pathlib import Path

from logslice.bookmarker import (
    Bookmark,
    save_bookmark,
    load_bookmark,
    list_bookmarks,
    delete_bookmark,
    read_from_bookmark,
)
from logslice.bookmark_reporter import report_bookmarks


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_save_list_report_plain(tmp_path):
    """Saving bookmarks and listing them produces a readable plain report."""
    for name, offset in [("start", 0), ("middle", 200), ("end", 800)]:
        save_bookmark(
            Bookmark(name=name, filepath="/app.log", offset=offset,
                     line_number=offset // 20 + 1, created_at=_now()),
            directory=tmp_path,
        )
    bms = list_bookmarks(directory=tmp_path)
    report = report_bookmarks(bms, fmt="plain")
    assert "start" in report
    assert "middle" in report
    assert "end" in report


def test_save_list_report_json(tmp_path):
    """JSON report contains all saved bookmarks."""
    names = ["alpha", "beta"]
    for name in names:
        save_bookmark(
            Bookmark(name=name, filepath="/x.log", offset=0,
                     line_number=1, created_at=_now()),
            directory=tmp_path,
        )
    bms = list_bookmarks(directory=tmp_path)
    data = json.loads(report_bookmarks(bms, fmt="json"))
    assert {d["name"] for d in data} == set(names)


def test_bookmark_and_resume(tmp_path):
    """Create a log, bookmark mid-file, resume reading from that point."""
    log = tmp_path / "service.log"
    lines = [f"line {i}\n" for i in range(10)]
    log.write_text("".join(lines))

    # Bookmark after first 5 lines
    offset = sum(len(l) for l in lines[:5])
    bm = Bookmark(
        name="mid", filepath=str(log), offset=offset,
        line_number=6, created_at=_now()
    )
    save_bookmark(bm, directory=tmp_path)

    loaded = load_bookmark("mid", directory=tmp_path)
    resumed = list(read_from_bookmark(str(log), loaded))
    assert len(resumed) == 5
    assert resumed[0].strip() == "line 5"


def test_delete_removes_from_list(tmp_path):
    """Deleting a bookmark removes it from the listing."""
    bm = Bookmark(name="temp", filepath="/f.log", offset=0,
                  line_number=1, created_at=_now())
    save_bookmark(bm, directory=tmp_path)
    assert len(list_bookmarks(directory=tmp_path)) == 1
    delete_bookmark("temp", directory=tmp_path)
    assert list_bookmarks(directory=tmp_path) == []
