"""Tests for logslice.profiler and logslice.profiler_reporter."""

import pytest
from logslice.profiler import ProfileResult, profile_lines, profile_iterable
from logslice.profiler_reporter import (
    format_profile_plain,
    format_profile_json,
    report_profile,
)
import json


# ---------------------------------------------------------------------------
# ProfileResult unit tests
# ---------------------------------------------------------------------------

class TestProfileResult:
    def test_zero_elapsed_lines_per_second(self):
        r = ProfileResult(total_lines=100, elapsed_seconds=0.0)
        assert r.lines_per_second == 0.0

    def test_zero_elapsed_bytes_per_second(self):
        r = ProfileResult(bytes_processed=500, elapsed_seconds=0.0)
        assert r.bytes_per_second == 0.0

    def test_zero_lines_avg_bytes(self):
        r = ProfileResult(total_lines=0, bytes_processed=0)
        assert r.avg_line_bytes == 0.0

    def test_lines_per_second_calculation(self):
        r = ProfileResult(total_lines=1000, elapsed_seconds=2.0)
        assert r.lines_per_second == pytest.approx(500.0)

    def test_bytes_per_second_calculation(self):
        r = ProfileResult(bytes_processed=2000, elapsed_seconds=4.0)
        assert r.bytes_per_second == pytest.approx(500.0)

    def test_avg_line_bytes(self):
        r = ProfileResult(total_lines=4, bytes_processed=40)
        assert r.avg_line_bytes == pytest.approx(10.0)

    def test_to_dict_keys(self):
        r = ProfileResult(total_lines=10, elapsed_seconds=1.0, bytes_processed=100)
        d = r.to_dict()
        assert set(d.keys()) == {
            "total_lines",
            "elapsed_seconds",
            "bytes_processed",
            "lines_per_second",
            "bytes_per_second",
            "avg_line_bytes",
        }


# ---------------------------------------------------------------------------
# profile_lines / profile_iterable
# ---------------------------------------------------------------------------

class TestProfileLines:
    def test_yields_all_lines_unchanged(self):
        src = ["alpha\n", "beta\n", "gamma\n"]
        gen, _ = profile_lines(src)
        assert list(gen) == src

    def test_counts_lines(self):
        src = ["a", "b", "c"]
        _, result = profile_iterable(src)
        assert result.total_lines == 3

    def test_counts_bytes(self):
        src = ["hello", "world"]  # 5 + 5 bytes
        _, result = profile_iterable(src)
        assert result.bytes_processed == 10

    def test_elapsed_is_positive(self):
        src = [str(i) for i in range(100)]
        _, result = profile_iterable(src)
        assert result.elapsed_seconds >= 0.0

    def test_empty_input(self):
        _, result = profile_iterable([])
        assert result.total_lines == 0
        assert result.bytes_processed == 0


# ---------------------------------------------------------------------------
# Reporter tests
# ---------------------------------------------------------------------------

class TestFormatProfilePlain:
    def _result(self):
        return ProfileResult(total_lines=200, elapsed_seconds=2.0, bytes_processed=4000)

    def test_title_in_output(self):
        out = format_profile_plain(self._result(), title="My Report")
        assert "My Report" in out

    def test_total_lines_shown(self):
        out = format_profile_plain(self._result())
        assert "200" in out

    def test_elapsed_shown(self):
        out = format_profile_plain(self._result())
        assert "2.000000" in out

    def test_lines_per_second_shown(self):
        out = format_profile_plain(self._result())
        assert "100.00" in out


class TestFormatProfileJson:
    def _result(self):
        return ProfileResult(total_lines=50, elapsed_seconds=1.0, bytes_processed=500)

    def test_valid_json(self):
        out = format_profile_json(self._result())
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_total_lines_field(self):
        out = format_profile_json(self._result())
        data = json.loads(out)
        assert data["total_lines"] == 50


class TestReportProfile:
    def test_plain_dispatch(self):
        r = ProfileResult(total_lines=1, elapsed_seconds=1.0, bytes_processed=5)
        out = report_profile(r, fmt="plain")
        assert "Profile Report" in out

    def test_json_dispatch(self):
        r = ProfileResult(total_lines=1, elapsed_seconds=1.0, bytes_processed=5)
        out = report_profile(r, fmt="json")
        assert json.loads(out)["total_lines"] == 1

    def test_unknown_format_raises(self):
        r = ProfileResult()
        with pytest.raises(ValueError, match="Unknown profile report format"):
            report_profile(r, fmt="xml")
