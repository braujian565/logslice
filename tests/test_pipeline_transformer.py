"""Tests for logslice.pipeline_transformer."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from logslice.pipeline_transformer import apply_transforms_from_config


def _cfg(**kwargs) -> SimpleNamespace:
    defaults = dict(
        transform_uppercase=False,
        transform_lowercase=False,
        transform_strip=False,
        transform_prefix=None,
        transform_suffix=None,
        transform_replace=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestApplyTransformsFromConfig:
    def test_no_transforms_yields_original(self):
        cfg = _cfg()
        lines = ["hello", "world"]
        assert list(apply_transforms_from_config(lines, cfg)) == ["hello", "world"]

    def test_uppercase_transform(self):
        cfg = _cfg(transform_uppercase=True)
        result = list(apply_transforms_from_config(["hello"], cfg))
        assert result == ["HELLO"]

    def test_lowercase_transform(self):
        cfg = _cfg(transform_lowercase=True)
        result = list(apply_transforms_from_config(["HELLO"], cfg))
        assert result == ["hello"]

    def test_uppercase_takes_precedence_over_lowercase(self):
        cfg = _cfg(transform_uppercase=True, transform_lowercase=True)
        result = list(apply_transforms_from_config(["hello"], cfg))
        assert result == ["HELLO"]

    def test_strip_transform(self):
        cfg = _cfg(transform_strip=True)
        result = list(apply_transforms_from_config(["  hi  "], cfg))
        assert result == ["hi"]

    def test_prefix_transform(self):
        cfg = _cfg(transform_prefix=">> ")
        result = list(apply_transforms_from_config(["msg"], cfg))
        assert result == [">> msg"]

    def test_suffix_transform(self):
        cfg = _cfg(transform_suffix=" <END>")
        result = list(apply_transforms_from_config(["msg"], cfg))
        assert result == ["msg <END>"]

    def test_replace_transform(self):
        cfg = _cfg(transform_replace=[(r"\d+", "NUM")])
        result = list(apply_transforms_from_config(["error 404"], cfg))
        assert result == ["error NUM"]

    def test_multiple_replace_rules(self):
        cfg = _cfg(transform_replace=[(r"\d+", "NUM"), (r"error", "ERR")])
        result = list(apply_transforms_from_config(["error 404"], cfg))
        assert result == ["ERR NUM"]

    def test_strip_then_prefix_order(self):
        cfg = _cfg(transform_strip=True, transform_prefix="- ")
        result = list(apply_transforms_from_config(["  line  "], cfg))
        assert result == ["- line"]

    def test_empty_lines_list(self):
        cfg = _cfg(transform_uppercase=True)
        assert list(apply_transforms_from_config([], cfg)) == []

    def test_missing_attributes_treated_as_disabled(self):
        cfg = SimpleNamespace()  # no transform_* attributes at all
        lines = ["keep me"]
        assert list(apply_transforms_from_config(lines, cfg)) == ["keep me"]
