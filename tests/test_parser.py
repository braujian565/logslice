"""Unit tests for logslice.parser."""

from datetime import datetime

import pytest

from logslice.parser import compile_pattern, extract_timestamp, matches_filter


class TestExtractTimestamp:
    def test_iso8601_with_T(self):
        line = '2024-03-15T12:34:56 ERROR something failed'
        ts = extract_timestamp(line)
        assert ts == datetime(2024, 3, 15, 12, 34, 56)

    def test_iso8601_space_separator(self):
        line = '2024-03-15 08:00:01 INFO server started'
        ts = extract_timestamp(line)
        assert ts == datetime(2024, 3, 15, 8, 0, 1)

    def test_syslog_format(self):
        line = 'Mar  5 09:15:30 myhost sshd[1234]: Accepted'
        ts = extract_timestamp(line)
        assert ts is not None
        assert ts.month == 3
        assert ts.day == 5

    def test_nginx_combined_log(self):
        line = '192.168.1.1 - - [15/Mar/2024:10:20:30 +0000] "GET / HTTP/1.1" 200 612'
        ts = extract_timestamp(line)
        assert ts == datetime(2024, 3, 15, 10, 20, 30)

    def test_no_timestamp_returns_none(self):
        line = 'This line has no timestamp at all'
        assert extract_timestamp(line) is None


class TestMatchesFilter:
    def test_no_pattern_always_matches(self):
        assert matches_filter('any line', None) is True

    def test_pattern_matches(self):
        import re
        p = re.compile(r'ERROR')
        assert matches_filter('2024-01-01 ERROR boom', p) is True

    def test_pattern_no_match(self):
        import re
        p = re.compile(r'CRITICAL')
        assert matches_filter('2024-01-01 INFO all good', p) is False


class TestCompilePattern:
    def test_none_returns_none(self):
        assert compile_pattern(None) is None

    def test_compiles_regex(self):
        p = compile_pattern(r'\d+')
        assert p is not None
        assert p.search('abc 123')

    def test_ignore_case_flag(self):
        import re
        p = compile_pattern('error', ignore_case=True)
        assert p.flags & re.IGNORECASE
        assert p.search('ERROR')
