"""Configuration dataclass for logslice.

Central place for all runtime options so that CLI, library callers, and
tests share a single source of truth.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import IO, Optional


@dataclass
class LogSliceConfig:
    """All options that control a logslice run."""

    # I/O
    input: IO = field(default_factory=lambda: sys.stdin)
    output: IO = field(default_factory=lambda: sys.stdout)

    # Filtering
    pattern: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Output format
    format: str = "plain"          # "plain" | "json"
    show_line_numbers: bool = False
    highlight: bool = False
    highlight_color: str = "yellow"

    # Sampling  (new)
    sample_rate: Optional[float] = None   # e.g. 0.1 → keep ~10 %
    sample_every: Optional[int] = None    # e.g. 10  → keep every 10th line
    sample_reservoir: Optional[int] = None  # e.g. 500 → reservoir of 500

    def is_filtered(self) -> bool:
        """Return True if any filtering or sampling option is active."""
        return any([
            self.pattern is not None,
            self.start_time is not None,
            self.end_time is not None,
            self.sample_rate is not None,
            self.sample_every is not None,
            self.sample_reservoir is not None,
        ])

    def validate(self) -> None:
        """Raise ValueError for invalid option combinations."""
        if self.format not in ("plain", "json"):
            raise ValueError(f"Unknown format {self.format!r}; expected 'plain' or 'json'")

        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time must not be later than end_time")

        sampling_opts = [
            self.sample_rate is not None,
            self.sample_every is not None,
            self.sample_reservoir is not None,
        ]
        if sum(sampling_opts) > 1:
            raise ValueError(
                "Only one sampling option may be specified at a time: "
                "sample_rate, sample_every, or sample_reservoir."
            )

        if self.sample_rate is not None and not (0.0 < self.sample_rate <= 1.0):
            raise ValueError(f"sample_rate must be in (0, 1], got {self.sample_rate!r}")

        if self.sample_every is not None and self.sample_every < 1:
            raise ValueError(f"sample_every must be >= 1, got {self.sample_every!r}")

        if self.sample_reservoir is not None and self.sample_reservoir < 1:
            raise ValueError(
                f"sample_reservoir must be >= 1, got {self.sample_reservoir!r}"
            )
