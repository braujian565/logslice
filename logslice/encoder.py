"""Line encoder: convert log lines to various byte encodings."""

from __future__ import annotations

import codecs
from typing import Iterable, Iterator

_SUPPORTED = {"utf-8", "utf-16", "latin-1", "ascii", "utf-8-sig"}


def _validate_encoding(encoding: str) -> str:
    """Normalise and validate an encoding name."""
    normalised = encoding.lower().replace("_", "-")
    try:
        codecs.lookup(normalised)
    except LookupError:
        raise ValueError(f"Unsupported encoding: {encoding!r}")
    return normalised


def encode_line(line: str, encoding: str = "utf-8", errors: str = "strict") -> bytes:
    """Encode a single log line to *bytes* using *encoding*."""
    enc = _validate_encoding(encoding)
    return line.encode(enc, errors=errors)


def decode_line(data: bytes, encoding: str = "utf-8", errors: str = "replace") -> str:
    """Decode *bytes* to a log line string."""
    enc = _validate_encoding(encoding)
    return data.decode(enc, errors=errors)


def encode_lines(
    lines: Iterable[str],
    encoding: str = "utf-8",
    errors: str = "strict",
    line_ending: str = "\n",
) -> Iterator[bytes]:
    """Yield each line encoded to bytes, appending *line_ending*."""
    enc = _validate_encoding(encoding)
    ending = line_ending.encode(enc)
    for line in lines:
        yield line.rstrip("\n").encode(enc, errors=errors) + ending


def decode_lines(
    chunks: Iterable[bytes],
    encoding: str = "utf-8",
    errors: str = "replace",
) -> Iterator[str]:
    """Yield each bytes chunk decoded to a string (newline stripped)."""
    enc = _validate_encoding(encoding)
    for chunk in chunks:
        yield chunk.decode(enc, errors=errors).rstrip("\n")


def transcode(
    lines: Iterable[str],
    source_encoding: str = "utf-8",
    target_encoding: str = "utf-8",
    errors: str = "replace",
) -> Iterator[str]:
    """Re-encode lines from *source_encoding* to *target_encoding*.

    Accepts str lines; round-trips through bytes to normalise encoding.
    """
    src = _validate_encoding(source_encoding)
    tgt = _validate_encoding(target_encoding)
    for line in lines:
        raw = line.encode(src, errors=errors)
        yield raw.decode(tgt, errors=errors)
