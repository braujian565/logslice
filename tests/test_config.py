"""Tests for logslice.config.LogSliceConfig."""

from datetime import datetime
import pytest
from logslice.config import LogSliceConfig


class TestLogSliceConfigDefaults:
    def test_default_input_is_stdin(self):
        cfg = LogSliceConfig()
        assert cfg.input_path == "-"

    def test_default_format_is_plain(self):
        cfg = LogSliceConfig()
        assert cfg.output_format == "plain"

    def test_highlight_off_by_default(self):
        cfg = LogSliceConfig()
        assert cfg.highlight is False

    def test_no_filters_by_default(self):
        cfg = LogSliceConfig()
        assert cfg.is_filtered() is False


class TestIsFiltered:
    def test_pattern_activates_filter(self):
        cfg = LogSliceConfig(pattern="ERROR")
        assert cfg.is_filtered() is True

    def test_start_time_activates_filter(self):
        cfg = LogSliceConfig(start_time=datetime(2024, 1, 1))
        assert cfg.is_filtered() is True

    def test_end_time_activates_filter(self):
        cfg = LogSliceConfig(end_time=datetime(2024, 12, 31))
        assert cfg.is_filtered() is True

    def test_multiple_filters(self):
        cfg = LogSliceConfig(pattern="WARN", start_time=datetime(2024, 6, 1))
        assert cfg.is_filtered() is True


class TestValidate:
    def test_valid_config_does_not_raise(self):
        cfg = LogSliceConfig(output_format="json", max_lines=10)
        cfg.validate()  # should not raise

    def test_invalid_format_raises(self):
        cfg = LogSliceConfig(output_format="xml")
        with pytest.raises(ValueError, match="Unknown output format"):
            cfg.validate()

    def test_start_after_end_raises(self):
        cfg = LogSliceConfig(
            start_time=datetime(2024, 12, 31),
            end_time=datetime(2024, 1, 1),
        )
        with pytest.raises(ValueError, match="start_time must not be later"):
            cfg.validate()

    def test_zero_max_lines_raises(self):
        cfg = LogSliceConfig(max_lines=0)
        with pytest.raises(ValueError, match="max_lines must be a positive integer"):
            cfg.validate()

    def test_negative_max_lines_raises(self):
        cfg = LogSliceConfig(max_lines=-5)
        with pytest.raises(ValueError, match="max_lines must be a positive integer"):
            cfg.validate()

    def test_invalid_highlight_color_raises(self):
        cfg = LogSliceConfig(highlight_color="purple")
        with pytest.raises(ValueError, match="Invalid highlight color"):
            cfg.validate()

    def test_valid_highlight_colors(self):
        for color in ("red", "green", "yellow", "blue", "magenta", "cyan", "bold"):
            cfg = LogSliceConfig(highlight_color=color)
            cfg.validate()  # should not raise
