"""Unit tests for logslice.slicer."""

import io
from datetime import datetime

import pytest

from logslice.parser import compile_pattern
from logslice.slicer import count_matches, slice_log

SAMPLE_LOG = """2024-03-15 08:00:00 INFO  server starting
2024-03-15 08:01:00 DEBUG config loaded
2024-03-15 08:02:00 ERROR disk full on /dev/sda1
2024-03-15 08:03:00 INFO  retrying operation
2024-03-15 08:04:00 WARN  memory usage at 90%
2024-03-15 08:05:00 ERROR connection refused
"""


def make_file(content: str) -> io.StringIO:
    return io.StringIO(content)


class TestSliceLog:
    def test_no_filters_returns_all_lines(self):
        lines = list(slice_log(make_file(SAMPLE_LOG)))
        assert len(lines) == 6

    def test_regex_filter(self):
        p = compile_pattern('ERROR')
        lines = list(slice_log(make_file(SAMPLE_LOG), pattern=p))
        assert len(lines) == 2
        assert all('ERROR' in l for l in lines)

    def test_start_time_filter(self):
        start = datetime(2024, 3, 15, 8, 3, 0)
        lines = list(slice_log(make_file(SAMPLE_LOG), start=start))
        assert len(lines) == 3
        assert '08:03:00' in lines[0]

    def test_end_time_filter(self):
        end = datetime(2024, 3, 15, 8, 2, 0)
        lines = list(slice_log(make_file(SAMPLE_LOG), end=end))
        assert len(lines) == 3

    def test_time_range_and_regex(self):
        start = datetime(2024, 3, 15, 8, 0, 0)
        end = datetime(2024, 3, 15, 8, 3, 0)
        p = compile_pattern('ERROR')
        lines = list(slice_log(make_file(SAMPLE_LOG), pattern=p, start=start, end=end))
        assert len(lines) == 1
        assert 'disk full' in lines[0]

    def test_empty_file(self):
        lines = list(slice_log(make_file('')))
        assert lines == []


class TestCountMatches:
    def test_count_all(self):
        assert count_matches(make_file(SAMPLE_LOG)) == 6

    def test_count_with_pattern(self):
        p = compile_pattern('WARN|ERROR')
        assert count_matches(make_file(SAMPLE_LOG), pattern=p) == 3
