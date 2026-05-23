"""Format and report ProfileResult objects as plain text or JSON."""

import json
from logslice.profiler import ProfileResult


def format_profile_plain(result: ProfileResult, title: str = "Profile Report") -> str:
    """Render a ProfileResult as a human-readable plain-text block."""
    lines = [
        f"=== {title} ===",
        f"  Total lines     : {result.total_lines:,}",
        f"  Bytes processed : {result.bytes_processed:,}",
        f"  Elapsed (s)     : {result.elapsed_seconds:.6f}",
        f"  Lines / sec     : {result.lines_per_second:,.2f}",
        f"  Bytes / sec     : {result.bytes_per_second:,.2f}",
        f"  Avg line bytes  : {result.avg_line_bytes:.2f}",
    ]
    return "\n".join(lines)


def format_profile_json(result: ProfileResult) -> str:
    """Render a ProfileResult as a compact JSON string."""
    return json.dumps(result.to_dict(), separators=(",", ":"))


def report_profile(
    result: ProfileResult,
    fmt: str = "plain",
    title: str = "Profile Report",
) -> str:
    """Dispatch to the appropriate formatter.

    Args:
        result: A populated ProfileResult.
        fmt:    'plain' or 'json'.
        title:  Heading used in plain output.

    Returns:
        Formatted string.

    Raises:
        ValueError: If fmt is not recognised.
    """
    if fmt == "plain":
        return format_profile_plain(result, title=title)
    if fmt == "json":
        return format_profile_json(result)
    raise ValueError(f"Unknown profile report format: {fmt!r}")
