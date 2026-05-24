"""Profiler module: measures parsing throughput and timing for log processing."""

import time
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Tuple


@dataclass
class ProfileResult:
    total_lines: int = 0
    elapsed_seconds: float = 0.0
    bytes_processed: int = 0

    @property
    def lines_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0.0
        return self.total_lines / self.elapsed_seconds

    @property
    def bytes_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0.0
        return self.bytes_processed / self.elapsed_seconds

    @property
    def avg_line_bytes(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.bytes_processed / self.total_lines

    def to_dict(self) -> dict:
        return {
            "total_lines": self.total_lines,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
            "bytes_processed": self.bytes_processed,
            "lines_per_second": round(self.lines_per_second, 2),
            "bytes_per_second": round(self.bytes_per_second, 2),
            "avg_line_bytes": round(self.avg_line_bytes, 2),
        }

    def __str__(self) -> str:
        """Return a human-readable summary of the profile result."""
        return (
            f"ProfileResult: {self.total_lines} lines, "
            f"{self.bytes_processed} bytes in {self.elapsed_seconds:.6f}s "
            f"({self.lines_per_second:.2f} lines/s, "
            f"{self.bytes_per_second:.2f} bytes/s)"
        )


def profile_lines(
    lines: Iterable[str],
) -> Tuple[Iterator[str], ProfileResult]:
    """Wrap an iterable of lines, tracking count, bytes, and elapsed time.

    Returns a generator that yields lines unchanged plus a ProfileResult
    object that is populated once the generator is exhausted.
    """
    result = ProfileResult()

    def _gen() -> Iterator[str]:
        result.elapsed_seconds = 0.0
        start = time.perf_counter()
        for line in lines:
            result.total_lines += 1
            result.bytes_processed += len(line.encode("utf-8", errors="replace"))
            yield line
        result.elapsed_seconds = time.perf_counter() - start

    return _gen(), result


def profile_iterable(lines: Iterable[str]) -> Tuple[list, ProfileResult]:
    """Eagerly consume lines, returning (list_of_lines, ProfileResult)."""
    gen, result = profile_lines(lines)
    collected = list(gen)
    return collected, result
