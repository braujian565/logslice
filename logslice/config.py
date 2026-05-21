"""Configuration dataclass for logslice run options."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LogSliceConfig:
    """Holds all runtime options for a logslice invocation."""

    # Input
    input_path: str = "-"  # "-" means stdin

    # Time range filters
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Pattern filter
    pattern: Optional[str] = None
    ignore_case: bool = False

    # Output options
    output_format: str = "plain"       # "plain" | "json"
    show_line_numbers: bool = False
    highlight: bool = False
    highlight_color: str = "yellow"

    # Behaviour
    count_only: bool = False
    max_lines: Optional[int] = None

    # Extra fields reserved for future use
    extra: dict = field(default_factory=dict)

    def is_filtered(self) -> bool:
        """Return True if any filter is active."""
        return any([
            self.start_time is not None,
            self.end_time is not None,
            self.pattern is not None,
        ])

    def validate(self) -> None:
        """Raise ValueError for invalid combinations."""
        if self.output_format not in ("plain", "json"):
            raise ValueError(f"Unknown output format: {self.output_format!r}")
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time must not be later than end_time")
        if self.max_lines is not None and self.max_lines < 1:
            raise ValueError("max_lines must be a positive integer")
        valid_colors = {"red", "green", "yellow", "blue", "magenta", "cyan", "bold"}
        if self.highlight_color not in valid_colors:
            raise ValueError(f"Invalid highlight color: {self.highlight_color!r}")
