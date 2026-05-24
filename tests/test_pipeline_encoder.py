"""Tests for logslice.pipeline_encoder."""

from types import SimpleNamespace

import pytest

from logslice.pipeline_encoder import apply_decoding_stage, apply_encoding_stage


def _cfg(**kwargs):
    defaults = {"encoding": "utf-8", "encoding_errors": "replace"}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestApplyEncodingStage:
    def test_plain_ascii_unchanged(self):
        cfg = _cfg()
        result = list(apply_encoding_stage(["hello", "world"], cfg))
        assert result == ["hello", "world"]

    def test_unicode_survives_utf8_roundtrip(self):
        cfg = _cfg()
        lines = ["caf\u00e9", "na\u00efve"]
        result = list(apply_encoding_stage(lines, cfg))
        assert result == lines

    def test_replace_errors_substitutes_bad_chars(self):
        cfg = _cfg(encoding="ascii", encoding_errors="replace")
        result = list(apply_encoding_stage(["caf\u00e9"], cfg))
        assert len(result) == 1
        assert "caf" in result[0]

    def test_empty_input_yields_nothing(self):
        cfg = _cfg()
        assert list(apply_encoding_stage([], cfg)) == []

    def test_missing_encoding_attr_defaults_to_utf8(self):
        cfg = SimpleNamespace()
        result = list(apply_encoding_stage(["hello"], cfg))
        assert result == ["hello"]

    def test_none_encoding_defaults_to_utf8(self):
        cfg = _cfg(encoding=None)
        result = list(apply_encoding_stage(["hello"], cfg))
        assert result == ["hello"]

    def test_latin1_encoding_used_when_configured(self):
        cfg = _cfg(encoding="latin-1", encoding_errors="replace")
        result = list(apply_encoding_stage(["caf\u00e9"], cfg))
        assert result == ["caf\u00e9"]

    def test_multiple_lines_all_processed(self):
        cfg = _cfg()
        lines = [f"line {i}" for i in range(20)]
        result = list(apply_encoding_stage(lines, cfg))
        assert result == lines


class TestApplyDecodingStage:
    def test_utf8_bytes_decoded(self):
        cfg = _cfg()
        chunks = [b"hello", b"world"]
        result = list(apply_decoding_stage(chunks, cfg))
        assert result == ["hello", "world"]

    def test_latin1_bytes_decoded(self):
        cfg = _cfg(encoding="latin-1")
        chunks = [b"caf\xe9"]
        result = list(apply_decoding_stage(chunks, cfg))
        assert result == ["caf\u00e9"]

    def test_invalid_bytes_replaced(self):
        cfg = _cfg(encoding="ascii", encoding_errors="replace")
        chunks = [b"\xff\xfe"]
        result = list(apply_decoding_stage(chunks, cfg))
        assert len(result) == 1

    def test_empty_input_yields_nothing(self):
        cfg = _cfg()
        assert list(apply_decoding_stage([], cfg)) == []

    def test_missing_encoding_attr_defaults_to_utf8(self):
        cfg = SimpleNamespace()
        result = list(apply_decoding_stage([b"hi"], cfg))
        assert result == ["hi"]
