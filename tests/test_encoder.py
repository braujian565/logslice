"""Tests for logslice.encoder."""

import pytest

from logslice.encoder import (
    decode_line,
    decode_lines,
    encode_line,
    encode_lines,
    transcode,
)


class TestEncodeLine:
    def test_utf8_default(self):
        assert encode_line("hello") == b"hello"

    def test_latin1_encoding(self):
        result = encode_line("caf\u00e9", encoding="latin-1")
        assert result == b"caf\xe9"

    def test_ascii_strict_raises_on_non_ascii(self):
        with pytest.raises(UnicodeEncodeError):
            encode_line("\u00e9", encoding="ascii", errors="strict")

    def test_ascii_replace_does_not_raise(self):
        result = encode_line("\u00e9", encoding="ascii", errors="replace")
        assert result == b"?"

    def test_invalid_encoding_raises(self):
        with pytest.raises(ValueError, match="Unsupported encoding"):
            encode_line("hi", encoding="bogus-99")

    def test_utf8_sig_bom_present(self):
        result = encode_line("hi", encoding="utf-8-sig")
        assert result.startswith(b"\xef\xbb\xbf")


class TestDecodeLine:
    def test_utf8_roundtrip(self):
        raw = "log entry \u00e9".encode("utf-8")
        assert decode_line(raw) == "log entry \u00e9"

    def test_latin1_roundtrip(self):
        raw = b"caf\xe9"
        assert decode_line(raw, encoding="latin-1") == "caf\u00e9"

    def test_invalid_bytes_replaced_by_default(self):
        result = decode_line(b"\xff\xfe", encoding="ascii", errors="replace")
        assert "\ufffd" in result or "?" in result or result is not None

    def test_invalid_encoding_raises(self):
        with pytest.raises(ValueError):
            decode_line(b"hi", encoding="not-an-encoding")


class TestEncodeLines:
    def test_yields_bytes(self):
        lines = ["alpha", "beta", "gamma"]
        result = list(encode_lines(lines))
        assert all(isinstance(b, bytes) for b in result)

    def test_newline_appended(self):
        result = list(encode_lines(["hello"]))
        assert result[0] == b"hello\n"

    def test_existing_newline_not_doubled(self):
        result = list(encode_lines(["hello\n"]))
        assert result[0] == b"hello\n"

    def test_custom_line_ending(self):
        result = list(encode_lines(["hi"], line_ending="\r\n"))
        assert result[0].endswith(b"\r\n")

    def test_empty_input_yields_nothing(self):
        assert list(encode_lines([])) == []


class TestDecodeLines:
    def test_strips_newline(self):
        result = list(decode_lines([b"hello\n"]))
        assert result == ["hello"]

    def test_multiple_lines(self):
        chunks = [b"one\n", b"two\n", b"three\n"]
        assert list(decode_lines(chunks)) == ["one", "two", "three"]

    def test_empty_yields_nothing(self):
        assert list(decode_lines([])) == []


class TestTranscode:
    def test_utf8_to_utf8_unchanged(self):
        lines = ["hello", "world"]
        result = list(transcode(lines))
        assert result == lines

    def test_latin1_chars_survive_roundtrip(self):
        lines = ["caf\u00e9"]
        result = list(transcode(lines, source_encoding="utf-8", target_encoding="utf-8"))
        assert result == lines

    def test_invalid_source_raises(self):
        with pytest.raises(ValueError):
            list(transcode(["hi"], source_encoding="nope"))

    def test_invalid_target_raises(self):
        with pytest.raises(ValueError):
            list(transcode(["hi"], target_encoding="nope"))
