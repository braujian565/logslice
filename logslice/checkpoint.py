"""Checkpoint support: persist and restore the last read position in a log file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional


DEFAULT_CHECKPOINT_DIR = Path.home() / ".logslice" / "checkpoints"


def _checkpoint_path(log_path: str, checkpoint_dir: Path) -> Path:
    """Return the checkpoint file path for a given log file."""
    safe_name = Path(log_path).resolve().as_posix().replace("/", "_").lstrip("_")
    return checkpoint_dir / f"{safe_name}.json"


def save_checkpoint(
    log_path: str,
    offset: int,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> None:
    """Persist *offset* (byte position) for *log_path* to disk."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    cp = _checkpoint_path(log_path, checkpoint_dir)
    data = {"log_path": log_path, "offset": offset}
    cp.write_text(json.dumps(data), encoding="utf-8")


def load_checkpoint(
    log_path: str,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> Optional[int]:
    """Return the saved byte offset for *log_path*, or ``None`` if not found."""
    cp = _checkpoint_path(log_path, checkpoint_dir)
    if not cp.exists():
        return None
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
        return int(data["offset"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def clear_checkpoint(
    log_path: str,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> bool:
    """Delete the checkpoint for *log_path*. Returns True if it existed."""
    cp = _checkpoint_path(log_path, checkpoint_dir)
    if cp.exists():
        cp.unlink()
        return True
    return False


def read_from_checkpoint(
    log_path: str,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
):
    """Yield lines from *log_path* starting at the saved checkpoint offset.

    After yielding all available lines the new file offset is returned via
    ``StopIteration`` value so callers can persist it with :func:`save_checkpoint`.
    """
    offset = load_checkpoint(log_path, checkpoint_dir) or 0
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(offset)
        for line in fh:
            yield line
        new_offset = fh.tell()
    save_checkpoint(log_path, new_offset, checkpoint_dir)
