"""Configuration dataclass for logslice."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import IO, List, Optional


@dataclass
class LogSliceConfig:
    # Input
    input: IO = field(default_factory=lambda: sys.stdin)
    input_path: Optional[str] = None

    # Filtering
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    # Output
    format: str = "plain"  # plain | json
    output: IO = field(default_factory=lambda: sys.stdout)
    output_path: Optional[str] = None

    # Display
    highlight: bool = False
    highlight_color: str = "yellow"
    line_numbers: bool = False
    context_before: int = 0
    context_after: int = 0

    # Sampling / dedup
    sample_rate: Optional[float] = None
    deduplicate: bool = False

    # Tail / watch
    tail: Optional[int] = None
    follow: bool = False

    # Redaction
    redact: List[str] = field(default_factory=list)
    redact_replacement: str = "[REDACTED]"

    def is_filtered(self) -> bool:
        return bool(
            self.include
            or self.exclude
            or self.start_time
            or self.end_time
        )

    def validate(self) -> None:
        allowed_formats = {"plain", "json"}
        if self.format not in allowed_formats:
            raise ValueError(
                f"format must be one of {allowed_formats}, got {self.format!r}"
            )
        if self.sample_rate is not None and not (0 < self.sample_rate <= 1):
            raise ValueError("sample_rate must be in (0, 1]")
        if self.context_before < 0:
            raise ValueError("context_before must be >= 0")
        if self.context_after < 0:
            raise ValueError("context_after must be >= 0")
        if self.tail is not None and self.tail < 0:
            raise ValueError("tail must be >= 0")
