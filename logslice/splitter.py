"""Split a log stream into multiple output files based on a regex pattern."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple


def split_by_pattern(
    lines: Iterable[str],
    pattern: str,
    group: int = 0,
) -> Dict[str, list]:
    """Partition *lines* into buckets keyed by a regex match.

    Args:
        lines:   Iterable of raw log lines.
        pattern: Regular expression to match against each line.
        group:   Capture group index whose value becomes the bucket key.
                 0 means the full match.

    Returns:
        A dict mapping each matched key to a list of lines that produced it.
        Lines that do not match are stored under the empty-string key ``""``.
    """
    compiled = re.compile(pattern)
    buckets: Dict[str, list] = defaultdict(list)
    for line in lines:
        m = compiled.search(line)
        if m:
            key = m.group(group)
        else:
            key = ""
        buckets[key].append(line)
    return dict(buckets)


def split_to_files(
    lines: Iterable[str],
    pattern: str,
    output_dir: str | Path,
    prefix: str = "part",
    group: int = 0,
    unmatched_name: Optional[str] = "unmatched.log",
) -> Dict[str, Path]:
    """Write bucketed lines to separate files inside *output_dir*.

    Args:
        lines:          Iterable of raw log lines.
        pattern:        Regex used to derive the bucket key.
        output_dir:     Directory that will contain the output files.
        prefix:         Filename prefix for matched buckets.
        group:          Capture group index (0 = full match).
        unmatched_name: Filename for lines that did not match.  Pass
                        ``None`` to discard unmatched lines silently.

    Returns:
        A dict mapping each bucket key to the ``Path`` of its output file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    buckets = split_by_pattern(lines, pattern, group)
    written: Dict[str, Path] = {}

    for key, bucket_lines in buckets.items():
        if key == "":
            if unmatched_name is None:
                continue
            file_path = out / unmatched_name
        else:
            safe_key = re.sub(r"[^\w\-]", "_", key)
            file_path = out / f"{prefix}_{safe_key}.log"

        with file_path.open("w", encoding="utf-8") as fh:
            fh.writelines(line if line.endswith("\n") else line + "\n"
                          for line in bucket_lines)

        written[key] = file_path

    return written


def iter_split(
    lines: Iterable[str],
    pattern: str,
    group: int = 0,
) -> Iterator[Tuple[str, str]]:
    """Yield ``(key, line)`` pairs without buffering all lines in memory."""
    compiled = re.compile(pattern)
    for line in lines:
        m = compiled.search(line)
        key = m.group(group) if m else ""
        yield key, line
