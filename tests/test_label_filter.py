"""Tests for logslice.label_filter."""

import pytest

from logslice.label_filter import drop_labeled, keep_labeled, prefix_label, strip_labels


def _labeled(*pairs):
    """Helper: build a list of (line, [label, ...]) tuples."""
    return list(pairs)


class TestKeepLabeled:
    def test_keeps_matching_label(self):
        data = _labeled(("line1", ["error"]), ("line2", ["warn"]))
        result = list(keep_labeled(data, ["error"]))
        assert result == [("line1", ["error"])]

    def test_keeps_multiple_labels(self):
        data = _labeled(("a", ["error"]), ("b", ["warn"]), ("c", ["info"]))
        result = list(keep_labeled(data, ["error", "warn"]))
        assert len(result) == 2

    def test_empty_keep_yields_nothing(self):
        data = _labeled(("a", ["error"]))
        assert list(keep_labeled(data, [])) == []

    def test_no_matching_label_yields_nothing(self):
        data = _labeled(("a", ["info"]))
        assert list(keep_labeled(data, ["error"])) == []


class TestDropLabeled:
    def test_drops_matching_label(self):
        data = _labeled(("a", ["error"]), ("b", ["info"]))
        result = list(drop_labeled(data, ["error"]))
        assert result == [("b", ["info"])]

    def test_empty_drop_keeps_all(self):
        data = _labeled(("a", ["error"]), ("b", ["info"]))
        assert list(drop_labeled(data, [])) == data

    def test_drops_multiple_labels(self):
        data = _labeled(("a", ["error"]), ("b", ["warn"]), ("c", ["info"]))
        result = list(drop_labeled(data, ["error", "warn"]))
        assert result == [("c", ["info"])]


class TestStripLabels:
    def test_yields_plain_lines(self):
        data = _labeled(("hello", ["error"]), ("world", []))
        assert list(strip_labels(data)) == ["hello", "world"]

    def test_empty_input(self):
        assert list(strip_labels([])) == []


class TestPrefixLabel:
    def test_prepends_first_label(self):
        data = _labeled(("msg", ["error"]))
        assert list(prefix_label(data)) == ["[error] msg"]

    def test_no_label_returns_line_unchanged(self):
        data = _labeled(("plain", []))
        assert list(prefix_label(data)) == ["plain"]

    def test_custom_separator(self):
        data = _labeled(("msg", ["warn"]))
        assert list(prefix_label(data, separator=": ")) == ["[warn]: msg"]

    def test_multi_label_uses_first(self):
        data = _labeled(("msg", ["error", "critical"]))
        assert list(prefix_label(data)) == ["[error] msg"]
