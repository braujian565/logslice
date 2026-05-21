"""Output formatters for logslice results."""

import json
from typing import Dict, Iterator, List, Optional, Tuple


def format_line_plain(
    line: str,
    line_number: Optional[int] = None,
) -> str:
    """Return a plain-text representation of a log line."""
    text = line.rstrip("\n")
    if line_number is not None:
        return f"{line_number}: {text}"
    return text


def format_line_json(
    line: str,
    line_number: Optional[int] = None,
    extra: Optional[Dict] = None,
) -> str:
    """Return a JSON-encoded representation of a log line."""
    obj: Dict = {"line": line.rstrip("\n")}
    if line_number is not None:
        obj["line_number"] = line_number
    if extra:
        obj.update(extra)
    return json.dumps(obj)


def format_summary(total: int, matched: int, label: str = "lines") -> str:
    """Return a human-readable match summary string."""
    return f"Matched {matched}/{total} {label}"


def format_aggregation(
    counts: Dict[str, int],
    title: str = "Aggregation",
    max_width: int = 40,
) -> str:
    """Render an aggregation dict as a formatted table string."""
    lines = [f"=== {title} ==="]
    if not counts:
        lines.append("  (no data)")
        return "\n".join(lines)
    max_val = max(counts.values(), default=1)
    for key, count in counts.items():
        bar_len = int((count / max_val) * max_width)
        bar = "#" * bar_len
        lines.append(f"  {key:<30} {count:>6}  {bar}")
    return "\n".join(lines)


def format_lines(
    lines: List[str],
    fmt: str = "plain",
    start_number: int = 1,
    show_numbers: bool = False,
) -> Iterator[str]:
    """Yield formatted versions of each line."""
    for i, line in enumerate(lines):
        num = start_number + i if show_numbers else None
        if fmt == "json":
            yield format_line_json(line, line_number=num)
        else:
            yield format_line_plain(line, line_number=num)


def format_context_block(
    block: List[Tuple[int, str, bool]],
    fmt: str = "plain",
    show_numbers: bool = True,
    match_marker: str = ">",
    context_marker: str = " ",
) -> Iterator[str]:
    """Yield formatted lines for a context block, marking matched vs context lines.

    Args:
        block: List of (line_index, line_text, is_match) tuples.
        fmt: Output format, 'plain' or 'json'.
        show_numbers: Whether to include 1-based line numbers.
        match_marker: Prefix character for matched lines.
        context_marker: Prefix character for context-only lines.
    """
    for idx, text, is_match in block:
        marker = match_marker if is_match else context_marker
        line_number = idx + 1 if show_numbers else None
        if fmt == "json":
            yield format_line_json(
                text,
                line_number=line_number,
                extra={"is_match": is_match},
            )
        else:
            num_str = f"{line_number}: " if line_number is not None else ""
            yield f"{marker} {num_str}{text.rstrip(chr(10))}"


def format_context_separator() -> str:
    """Return the standard separator string between non-adjacent context blocks."""
    return "--"
