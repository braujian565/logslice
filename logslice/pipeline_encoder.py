"""Pipeline integration for the encoder: apply encoding/decoding stages from config."""

from __future__ import annotations

from typing import Iterable, Iterator

from logslice.encoder import decode_line, encode_line


def _encoding_from_config(cfg) -> str:
    """Extract the target encoding from a config object (default utf-8)."""
    return getattr(cfg, "encoding", "utf-8") or "utf-8"


def _errors_from_config(cfg) -> str:
    """Extract the error-handling strategy from config (default replace)."""
    return getattr(cfg, "encoding_errors", "replace") or "replace"


def apply_encoding_stage(
    lines: Iterable[str],
    cfg,
) -> Iterator[str]:
    """Round-trip each line through the configured encoding.

    Lines that cannot be encoded cleanly are handled according to
    *cfg.encoding_errors* (default: ``'replace'``).
    """
    encoding = _encoding_from_config(cfg)
    errors = _errors_from_config(cfg)

    for line in lines:
        raw = encode_line(line, encoding=encoding, errors=errors)
        yield decode_line(raw, encoding=encoding, errors=errors)


def apply_decoding_stage(
    chunks: Iterable[bytes],
    cfg,
) -> Iterator[str]:
    """Decode raw byte chunks to strings using the configured encoding."""
    encoding = _encoding_from_config(cfg)
    errors = _errors_from_config(cfg)

    for chunk in chunks:
        yield decode_line(chunk, encoding=encoding, errors=errors)
